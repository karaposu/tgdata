"""
Data models for the Telegram Group Message Crawler.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Any, Dict



@dataclass
class RateLimitInfo:
    """Track rate limit information"""
    requests_made: int = 0
    window_start: float = 0
    last_request: float = 0
    flood_wait_until: float = 0


@dataclass
class GroupInfo:
    """Information about a Telegram group/channel"""
    id: int
    title: str
    username: Optional[str] = None
    is_channel: bool = False
    is_megagroup: bool = False
    participants_count: Optional[int] = None


@dataclass
class MessageData:
    """Structured message data"""
    message_id: int
    sender_id: int
    sender_name: str
    username: Optional[str]  # '@handle' or None (no public username)
    message: Optional[str]
    date: datetime
    reply_to_id: Optional[int] = None
    forwarded_from: Optional[int] = None
    photo_data: Optional[bytes] = None
    chat_id: Optional[int] = None        # bare group/channel id (matches list_groups' GroupID)
    media_type: Optional[str] = None     # 'photo', 'video', 'document', ...; None = text-only
    grouped_id: Optional[int] = None     # album tag: messages sharing it form one multi-media post
    message_link: Optional[str] = None   # t.me deep link to the original message (None if not linkable)
    media_path: Optional[str] = None     # local file path if media was downloaded during fetch, else None
    media_data: Optional[bytes] = None   # raw media bytes in-memory if include_media=True, else None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for DataFrame creation"""
        return {
            'MessageId': self.message_id,
            'ChatId': self.chat_id,
            'SenderId': self.sender_id,
            'Name': self.sender_name,
            'Username': self.username,
            'Message': self.message,
            'MediaType': self.media_type,
            'GroupedId': self.grouped_id,
            'MediaPath': self.media_path,
            'Date': self.date,
            'ReplyToId': self.reply_to_id,
            'ForwardedFrom': self.forwarded_from,
            'MessageLink': self.message_link,
            'MediaData': self.media_data,
            'PhotoData': self.photo_data
        }


@dataclass
class ConnectionConfig:
    """Configuration for Telegram connection"""
    api_id: str
    api_hash: str
    session_file: str
    phone: Optional[str] = None
    username: Optional[str] = None
    max_retries: int = 3
    retry_delay: float = 1.0
    exponential_backoff: bool = True