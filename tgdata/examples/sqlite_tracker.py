"""
Example SQLite implementation of MessageTrackerInterface.

This shows how users can implement their own persistent message tracking
using the MessageTrackerInterface from the telegram-group-message-crawler package.
"""

import sqlite3
import json
from datetime import datetime
from typing import Optional, List, Dict, Any
from contextlib import contextmanager
import logging

# Import from the package
from tgdata.message_tracker_interface import MessageTrackerInterface, MessageInfo

logger = logging.getLogger(__name__)


class SQLiteTracker(MessageTrackerInterface):
    """
    SQLite-based implementation of MessageTrackerInterface.
    
    Provides persistent message tracking with checkpointing support.
    """
    
    def __init__(self, db_path: str = "message_tracking.db"):
        """
        Initialize SQLite tracker.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self._init_database()
        self._cache = set()  # Small cache for performance
        self._cache_size = 10000
        self._load_cache()
        
    def _init_database(self):
        """Initialize database tables."""
        with self._get_connection() as conn:
            # Messages table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS processed_messages (
                    message_id INTEGER,
                    group_id INTEGER,
                    sender_id INTEGER,
                    date TIMESTAMP,
                    processed_at TIMESTAMP,
                    content_hash TEXT,
                    PRIMARY KEY (message_id, group_id)
                )
            """)
            
            # Checkpoints table for resumable operations
            conn.execute("""
                CREATE TABLE IF NOT EXISTS checkpoints (
                    checkpoint_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    operation_id TEXT UNIQUE,
                    group_id INTEGER,
                    last_message_id INTEGER,
                    last_message_date TIMESTAMP,
                    total_processed INTEGER,
                    created_at TIMESTAMP,
                    metadata TEXT
                )
            """)
            
            # Create indexes
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_processed_group 
                ON processed_messages(group_id, date)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_checkpoints_operation 
                ON checkpoints(operation_id)
            """)
            
            conn.commit()
            
    @contextmanager
    def _get_connection(self):
        """Get database connection with context manager."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
            
    def _load_cache(self):
        """Load recent message IDs into memory cache for performance."""
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT message_id, group_id FROM processed_messages 
                ORDER BY processed_at DESC 
                LIMIT ?
            """, (self._cache_size,))
            
            self._cache = {(row['message_id'], row['group_id']) for row in cursor}
            
    async def is_processed(self, message_id: int, group_id: int) -> bool:
        """Check if a message has been processed."""
        # Check cache first
        if (message_id, group_id) in self._cache:
            return True
            
        # Check database
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT 1 FROM processed_messages 
                WHERE message_id = ? AND group_id = ?
            """, (message_id, group_id))
            
            return cursor.fetchone() is not None
            
    async def mark_processed(self, message_info: MessageInfo) -> None:
        """Mark a message as processed."""
        with self._get_connection() as conn:
            try:
                conn.execute("""
                    INSERT INTO processed_messages 
                    (message_id, group_id, sender_id, date, processed_at, content_hash)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    message_info.message_id,
                    message_info.group_id,
                    message_info.sender_id,
                    message_info.date,
                    datetime.now(),
                    message_info.content_hash
                ))
                
                conn.commit()
                
                # Update cache
                self._cache.add((message_info.message_id, message_info.group_id))
                
                # Trim cache if too large
                if len(self._cache) > self._cache_size * 1.5:
                    self._load_cache()
                    
            except sqlite3.IntegrityError:
                # Message already processed
                pass
                
    async def mark_batch_processed(self, messages: List[MessageInfo]) -> None:
        """Mark multiple messages as processed in a batch."""
        with self._get_connection() as conn:
            data = [
                (
                    msg.message_id,
                    msg.group_id,
                    msg.sender_id,
                    msg.date,
                    datetime.now(),
                    msg.content_hash
                )
                for msg in messages
            ]
            
            conn.executemany("""
                INSERT OR IGNORE INTO processed_messages 
                (message_id, group_id, sender_id, date, processed_at, content_hash)
                VALUES (?, ?, ?, ?, ?, ?)
            """, data)
            
            conn.commit()
            
            # Update cache
            for msg in messages:
                self._cache.add((msg.message_id, msg.group_id))
                
    async def get_unprocessed(self, messages: List[Dict[str, Any]], group_id: int) -> List[Dict[str, Any]]:
        """Filter out already processed messages."""
        unprocessed = []
        
        for msg in messages:
            msg_id = msg.get('MessageId', msg.get('message_id'))
            if msg_id and not await self.is_processed(msg_id, group_id):
                unprocessed.append(msg)
                
        logger.info(f"Filtered {len(messages) - len(unprocessed)} duplicate messages")
        return unprocessed
        
    async def get_stats(self, group_id: Optional[int] = None) -> Dict[str, Any]:
        """Get processing statistics."""
        with self._get_connection() as conn:
            if group_id:
                # Stats for specific group
                cursor = conn.execute("""
                    SELECT COUNT(*) as total,
                           MIN(date) as first_message,
                           MAX(date) as last_message,
                           COUNT(DISTINCT sender_id) as unique_senders
                    FROM processed_messages
                    WHERE group_id = ?
                """, (group_id,))
            else:
                # Overall stats
                cursor = conn.execute("""
                    SELECT COUNT(*) as total,
                           MIN(date) as first_message,
                           MAX(date) as last_message,
                           COUNT(DISTINCT sender_id) as unique_senders,
                           COUNT(DISTINCT group_id) as total_groups
                    FROM processed_messages
                """)
                
            row = cursor.fetchone()
            
            stats = {
                "total_processed": row['total'] or 0,
                "first_message_date": row['first_message'],
                "last_message_date": row['last_message'],
                "unique_senders": row['unique_senders'] or 0,
                "implementation": "SQLiteTracker",
                "cache_size": len(self._cache)
            }
            
            if not group_id and 'total_groups' in row:
                stats['total_groups'] = row['total_groups'] or 0
                
            return stats
            
    # Additional SQLite-specific methods
    
    def save_checkpoint(self,
                       operation_id: str,
                       group_id: int,
                       last_message_id: int,
                       last_message_date: datetime,
                       total_processed: int,
                       metadata: Optional[Dict[str, Any]] = None):
        """
        Save a checkpoint for resumable operations.
        
        Args:
            operation_id: Unique identifier for the operation
            group_id: Telegram group ID
            last_message_id: ID of last processed message
            last_message_date: Date of last processed message
            total_processed: Total messages processed so far
            metadata: Additional metadata to store
        """
        with self._get_connection() as conn:
            metadata_json = json.dumps(metadata) if metadata else None
            
            conn.execute("""
                INSERT OR REPLACE INTO checkpoints
                (operation_id, group_id, last_message_id, last_message_date, 
                 total_processed, created_at, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (operation_id, group_id, last_message_id, last_message_date,
                  total_processed, datetime.now(), metadata_json))
            
            conn.commit()
            
        logger.info(f"Saved checkpoint for operation {operation_id}: "
                   f"message_id={last_message_id}, total={total_processed}")
                   
    def load_checkpoint(self, operation_id: str) -> Optional[Dict[str, Any]]:
        """
        Load a checkpoint for resuming operations.
        
        Args:
            operation_id: Unique identifier for the operation
            
        Returns:
            Checkpoint data if found, None otherwise
        """
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM checkpoints
                WHERE operation_id = ?
                ORDER BY created_at DESC
                LIMIT 1
            """, (operation_id,))
            
            row = cursor.fetchone()
            
            if row:
                metadata = json.loads(row['metadata']) if row['metadata'] else None
                
                return {
                    'group_id': row['group_id'],
                    'last_message_id': row['last_message_id'],
                    'last_message_date': datetime.fromisoformat(row['last_message_date']),
                    'total_processed': row['total_processed'],
                    'operation_id': row['operation_id'],
                    'created_at': datetime.fromisoformat(row['created_at']),
                    'metadata': metadata
                }
                
        return None
        
    def cleanup_old_records(self, days_to_keep: int = 90):
        """
        Clean up old tracking records.
        
        Args:
            days_to_keep: Keep records from last N days
        """
        cutoff_date = datetime.now().timestamp() - (days_to_keep * 86400)
        
        with self._get_connection() as conn:
            conn.execute("""
                DELETE FROM processed_messages
                WHERE date < datetime(?, 'unixepoch')
            """, (cutoff_date,))
            
            deleted = conn.total_changes
            conn.commit()
            
        logger.info(f"Cleaned up {deleted} old message records")
        self._load_cache()  # Reload cache


# Example usage
if __name__ == "__main__":
    import asyncio
    
    async def example():
        # Create tracker
        tracker = SQLiteTracker("my_messages.db")
        
        # Check if message processed
        is_processed = await tracker.is_processed(12345, 1001)
        print(f"Message processed: {is_processed}")
        
        # Mark message as processed
        msg_info = MessageInfo(
            message_id=12345,
            group_id=1001,
            sender_id=5678,
            date=datetime.now()
        )
        await tracker.mark_processed(msg_info)
        
        # Get stats
        stats = await tracker.get_stats()
        print(f"Stats: {stats}")
        
    asyncio.run(example())