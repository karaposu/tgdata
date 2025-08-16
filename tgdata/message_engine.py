"""
Message processing engine for Telegram.
Handles message fetching, filtering, deduplication, and formatting.
"""

import asyncio
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any, Callable
import pandas as pd
from telethon.errors import FloodWaitError

from .connection_engine import ConnectionEngine
from .models import MessageInfo, MessageData
from .message_tracker_interface import MessageTrackerInterface, InMemoryTracker
from .progress import ProgressTracker

logger = logging.getLogger(__name__)


class MessageEngine:
    """
    Handles all message-related operations.
    """
    
    def __init__(self,
                 connection_engine: ConnectionEngine,
                 tracker: Optional[MessageTrackerInterface] = None,
                 enable_deduplication: bool = True):
        """
        Initialize message engine.
        
        Args:
            connection_engine: Connection engine instance
            tracker: Optional message tracker for deduplication
            enable_deduplication: Whether to enable deduplication
        """
        self.connection_engine = connection_engine
        self.enable_deduplication = enable_deduplication
        
        # Set up tracker
        if enable_deduplication:
            self.tracker = tracker or InMemoryTracker()
        else:
            self.tracker = None
            
        # Message cache for performance
        self._message_cache: Dict[str, pd.DataFrame] = {}
        
    async def fetch_messages(self,
                           group_id: int,
                           limit: Optional[int] = None,
                           start_date: Optional[datetime] = None,
                           end_date: Optional[datetime] = None,
                           include_profile_photos: bool = False,
                           use_cache: bool = True,
                           progress_callback: Optional[Callable] = None,
                           min_id: Optional[int] = None) -> pd.DataFrame:
        """
        Fetch messages from a group with various filters.
        
        Args:
            group_id: Telegram group/channel ID
            limit: Maximum number of messages to fetch
            start_date: Get messages after this date
            end_date: Get messages before this date
            include_profile_photos: Whether to download profile photos
            use_cache: Whether to use cached results
            progress_callback: Optional callback for progress updates
            min_id: Minimum message ID (for resuming)
            
        Returns:
            DataFrame with messages
        """
        # Check cache
        cache_key = f"{group_id}_{start_date}_{end_date}_{limit}"
        if use_cache and cache_key in self._message_cache:
            logger.info("Returning cached messages")
            return self._message_cache[cache_key]
            
        # Set up progress tracking
        progress_tracker = None
        if progress_callback:
            progress_tracker = ProgressTracker(
                total_expected=limit,
                callback=progress_callback
            )
            progress_tracker.start()
            
        messages_data = []
        processed_count = 0
        
        try:
            client = await self.connection_engine.get_client()
            
            async with client:
                # Get the entity
                channel = await client.get_entity(group_id)
                logger.info(f"Fetching messages from: {channel.title}")
                
                # Determine iteration parameters
                offset_date = end_date if end_date else datetime.now()
                reverse = bool(start_date)  # Reverse if we have a start date
                
                # Build kwargs for iter_messages
                iter_kwargs = {
                    'entity': channel,
                    'limit': limit,
                    'offset_date': offset_date,
                    'reverse': reverse
                }
                
                # Only add min_id if it's not None
                if min_id is not None:
                    iter_kwargs['min_id'] = min_id
                
                # Iterate through messages
                async for msg in client.iter_messages(**iter_kwargs):
                    # Apply date filters
                    if start_date and msg.date < start_date:
                        continue
                    if end_date and msg.date > end_date:
                        break
                        
                    # Check deduplication
                    if self.enable_deduplication and self.tracker:
                        if await self.tracker.is_processed(msg.id, group_id):
                            logger.debug(f"Skipping duplicate message {msg.id}")
                            continue
                            
                    # Process message
                    message_data = await self._process_message(
                        msg, 
                        client,
                        include_profile_photos
                    )
                    
                    if message_data:
                        messages_data.append(message_data.to_dict())
                        
                        # Track processed message
                        if self.tracker:
                            await self.tracker.mark_processed(
                                MessageInfo(
                                    message_id=msg.id,
                                    group_id=group_id,
                                    sender_id=message_data.sender_id,
                                    date=msg.date
                                )
                            )
                            
                        processed_count += 1
                        
                        # Update progress
                        if progress_tracker:
                            progress_tracker.update()
                            
                        # Log progress
                        if processed_count % 100 == 0:
                            logger.info(f"Processed {processed_count} messages...")
                            
        except FloodWaitError as e:
            await self.connection_engine.handle_rate_limit(e, client)
            # Retry after rate limit
            return await self.fetch_messages(
                group_id=group_id,
                limit=limit,
                start_date=start_date,
                end_date=end_date,
                include_profile_photos=include_profile_photos,
                use_cache=use_cache,
                progress_callback=progress_callback,
                min_id=min_id
            )
            
        except Exception as e:
            logger.error(f"Error fetching messages: {e}")
            raise
            
        # Create DataFrame
        df = pd.DataFrame(messages_data)
        
        # Cache results
        if use_cache and not df.empty:
            self._message_cache[cache_key] = df
            
        logger.info(f"Retrieved {len(df)} messages")
        
        # Log tracker stats
        if self.tracker:
            stats = await self.tracker.get_stats(group_id)
            logger.info(f"Tracker stats: {stats}")
            
        return df
        
    async def _process_message(self,
                             msg,
                             client,
                             include_profile_photos: bool) -> Optional[MessageData]:
        """Process a single message"""
        try:
            sender = await msg.get_sender()
            if not sender:
                return None
                
            # Extract sender info
            sender_name = f"{getattr(sender, 'first_name', '') or ''} {getattr(sender, 'last_name', '') or ''}".strip()
            username = f"@{sender.username}" if hasattr(sender, 'username') and sender.username else "No username"
            
            # Create message data
            message_data = MessageData(
                message_id=msg.id,
                sender_id=sender.id,
                sender_name=sender_name,
                username=username,
                message=msg.message,
                date=msg.date,
                reply_to_id=msg.reply_to_msg_id,
                forwarded_from=msg.fwd_from.from_id if msg.fwd_from else None
            )
            
            # Download profile photo if requested
            if include_profile_photos and hasattr(sender, 'photo') and sender.photo:
                try:
                    photo_bytes = await client.download_profile_photo(sender, file=bytes)
                    message_data.photo_data = photo_bytes
                except Exception as e:
                    logger.warning(f"Failed to download photo for {sender.id}: {e}")
                    
            return message_data
            
        except Exception as e:
            logger.error(f"Error processing message {msg.id}: {e}")
            return None
            
        
    def clear_cache(self, group_id: Optional[int] = None):
        """
        Clear message cache.
        
        Args:
            group_id: Optional group ID to clear cache for specific group
        """
        if group_id:
            # Clear cache for specific group
            keys_to_remove = [k for k in self._message_cache.keys() if k.startswith(f"{group_id}_")]
            for key in keys_to_remove:
                del self._message_cache[key]
            logger.info(f"Cleared cache for group {group_id}")
        else:
            # Clear all cache
            self._message_cache.clear()
            logger.info("Cleared all message cache")
            
    async def get_message_count(self, group_id: int) -> int:
        """
        Get total message count for a group.
        
        Args:
            group_id: Telegram group/channel ID
            
        Returns:
            Total message count
        """
        try:
            client = await self.connection_engine.get_client()
            
            async with client:
                # Get the messages with limit=1 to access count
                messages = await client.get_messages(group_id, limit=1)
                
                # TotalList objects have a 'total' attribute
                if hasattr(messages, 'total'):
                    return messages.total
                else:
                    # If it's just a regular list, we can't get total efficiently
                    logger.warning("Could not get message count efficiently")
                    return 0
                    
        except Exception as e:
            logger.error(f"Error getting message count: {e}")
            raise
            
    async def search_messages(self,
                            group_id: int,
                            query: str,
                            limit: Optional[int] = None) -> pd.DataFrame:
        """
        Search for messages containing specific text.
        
        Args:
            group_id: Telegram group/channel ID
            query: Search query
            limit: Maximum number of results
            
        Returns:
            DataFrame with matching messages
        """
        try:
            client = await self.connection_engine.get_client()
            messages_data = []
            
            async with client:
                channel = await client.get_entity(group_id)
                
                async for msg in client.iter_messages(
                    channel,
                    search=query,
                    limit=limit
                ):
                    message_data = await self._process_message(msg, client, False)
                    if message_data:
                        messages_data.append(message_data.to_dict())
                        
            df = pd.DataFrame(messages_data)
            logger.info(f"Found {len(df)} messages matching '{query}'")
            return df
            
        except Exception as e:
            logger.error(f"Error searching messages: {e}")
            raise