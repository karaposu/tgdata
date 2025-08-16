"""
Message tracking interface and implementations for the Telegram Group Message Crawler.
This provides a clean abstraction for tracking processed messages without forcing
a specific storage backend.
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any, Set, Tuple
from datetime import datetime
import logging

from .models import MessageInfo

logger = logging.getLogger(__name__)


class MessageTrackerInterface(ABC):
    """
    Abstract interface for message tracking.
    
    Users can implement this interface with their preferred storage backend:
    - SQLite, PostgreSQL, MySQL
    - Redis, Memcached
    - MongoDB, DynamoDB
    - In-memory (provided)
    """
    
    @abstractmethod
    async def is_processed(self, message_id: int, group_id: int) -> bool:
        """
        Check if a message has been processed.
        
        Args:
            message_id: Telegram message ID
            group_id: Telegram group ID
            
        Returns:
            True if message was already processed
        """
        pass
    
    @abstractmethod
    async def mark_processed(self, message_info: MessageInfo) -> None:
        """
        Mark a message as processed.
        
        Args:
            message_info: Information about the message
        """
        pass
    
    @abstractmethod
    async def mark_batch_processed(self, messages: List[MessageInfo]) -> None:
        """
        Mark multiple messages as processed in a batch.
        
        Args:
            messages: List of message information
        """
        pass
    
    @abstractmethod
    async def get_unprocessed(self, messages: List[Dict[str, Any]], group_id: int) -> List[Dict[str, Any]]:
        """
        Filter out already processed messages from a list.
        
        Args:
            messages: List of message dictionaries
            group_id: Telegram group ID
            
        Returns:
            List of unprocessed messages
        """
        pass
    
    async def get_stats(self, group_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Get processing statistics (optional to implement).
        
        Args:
            group_id: Optional group ID to filter stats
            
        Returns:
            Dictionary with statistics
        """
        return {"total_processed": 0, "implementation": self.__class__.__name__}


class InMemoryTracker(MessageTrackerInterface):
    """
    Simple in-memory implementation of MessageTrackerInterface.
    
    Good for:
    - Development and testing
    - Small-scale operations
    - Temporary tracking within a session
    
    Limitations:
    - No persistence between runs
    - Memory usage grows with tracked messages
    - No distributed/shared state
    """
    
    def __init__(self, max_size: Optional[int] = None):
        """
        Initialize in-memory tracker.
        
        Args:
            max_size: Optional maximum number of messages to track (LRU eviction)
        """
        self._processed: Set[Tuple[int, int]] = set()
        self._message_info: Dict[Tuple[int, int], MessageInfo] = {}
        self._max_size = max_size
        self._access_order: List[Tuple[int, int]] = []
        
    async def is_processed(self, message_id: int, group_id: int) -> bool:
        """Check if message is processed."""
        key = (message_id, group_id)
        is_in = key in self._processed
        
        if is_in and self._max_size:
            # Update access order for LRU
            self._access_order.remove(key)
            self._access_order.append(key)
            
        return is_in
    
    async def mark_processed(self, message_info: MessageInfo) -> None:
        """Mark message as processed."""
        key = (message_info.message_id, message_info.group_id)
        
        # Add to processed set
        self._processed.add(key)
        self._message_info[key] = message_info
        self._access_order.append(key)
        
        # Evict old entries if needed
        if self._max_size and len(self._processed) > self._max_size:
            # Remove least recently used
            lru_key = self._access_order.pop(0)
            self._processed.remove(lru_key)
            del self._message_info[lru_key]
            
        logger.debug(f"Marked message {message_info.message_id} as processed")
    
    async def mark_batch_processed(self, messages: List[MessageInfo]) -> None:
        """Mark multiple messages as processed."""
        for msg in messages:
            await self.mark_processed(msg)
            
    async def get_unprocessed(self, messages: List[Dict[str, Any]], group_id: int) -> List[Dict[str, Any]]:
        """Filter out processed messages."""
        unprocessed = []
        
        for msg in messages:
            msg_id = msg.get('MessageId', msg.get('message_id'))
            if msg_id and not await self.is_processed(msg_id, group_id):
                unprocessed.append(msg)
                
        logger.info(f"Filtered {len(messages) - len(unprocessed)} duplicate messages")
        return unprocessed
    
    async def get_stats(self, group_id: Optional[int] = None) -> Dict[str, Any]:
        """Get tracking statistics."""
        if group_id:
            count = sum(1 for (_, gid) in self._processed if gid == group_id)
        else:
            count = len(self._processed)
            
        return {
            "total_processed": count,
            "implementation": "InMemoryTracker",
            "max_size": self._max_size,
            "current_size": len(self._processed)
        }
    
    def clear(self):
        """Clear all tracked messages."""
        self._processed.clear()
        self._message_info.clear()
        self._access_order.clear()


class NoOpTracker(MessageTrackerInterface):
    """
    No-operation tracker that doesn't actually track anything.
    Useful for disabling deduplication entirely.
    """
    
    async def is_processed(self, message_id: int, group_id: int) -> bool:
        """Always returns False (nothing is tracked)."""
        return False
    
    async def mark_processed(self, message_info: MessageInfo) -> None:
        """Does nothing."""
        pass
    
    async def mark_batch_processed(self, messages: List[MessageInfo]) -> None:
        """Does nothing."""
        pass
    
    async def get_unprocessed(self, messages: List[Dict[str, Any]], group_id: int) -> List[Dict[str, Any]]:
        """Returns all messages (nothing is filtered)."""
        return messages
    
    async def get_stats(self, group_id: Optional[int] = None) -> Dict[str, Any]:
        """Returns empty stats."""
        return {"total_processed": 0, "implementation": "NoOpTracker"}


# Example of how users would implement their own tracker
"""
Example implementation for SQLite (to be placed in user's code):

class SQLiteTracker(MessageTrackerInterface):
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_db()
        
    def _init_db(self):
        import sqlite3
        conn = sqlite3.connect(self.db_path)
        conn.execute('''
            CREATE TABLE IF NOT EXISTS processed_messages (
                message_id INTEGER,
                group_id INTEGER,
                sender_id INTEGER,
                date TIMESTAMP,
                PRIMARY KEY (message_id, group_id)
            )
        ''')
        conn.commit()
        conn.close()
        
    async def is_processed(self, message_id: int, group_id: int) -> bool:
        import sqlite3
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute(
            "SELECT 1 FROM processed_messages WHERE message_id = ? AND group_id = ?",
            (message_id, group_id)
        )
        result = cursor.fetchone() is not None
        conn.close()
        return result
        
    # ... implement other methods
"""