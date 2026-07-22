"""
Message processing engine for Telegram.
Handles message fetching, filtering, deduplication, and formatting.
"""

import asyncio
import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict, Any, Callable, Iterable, Union
import pandas as pd
from telethon import utils as tl_utils
from telethon.errors import FloodWaitError
from telethon.tl import types as tl_types

from .connection_engine import ConnectionEngine
from .models import MessageData
from .progress import ProgressTracker

logger = logging.getLogger(__name__)

# Safety bound for fetches that specify no limit: prevents an accidental
# full-history walk on huge groups. Hitting it logs a warning; callers lift
# it with an explicit limit=... or allow_full_fetch=True.
DEFAULT_FETCH_LIMIT = 750

# How many FloodWait (rate-limit) interruptions to wait out and resume from
# before giving up with a clear error.
MAX_FLOOD_RETRIES = 3


class MessageEngine:
    """
    Handles all message-related operations.
    """

    def __init__(self,
                 connection_engine: ConnectionEngine):
        """
        Initialize message engine.

        Args:
            connection_engine: Connection engine instance
        """
        self.connection_engine = connection_engine

    async def fetch_messages(self,
                           group_id: int,
                           limit: Optional[int] = None,
                           start_date: Optional[datetime] = None,
                           end_date: Optional[datetime] = None,
                           include_profile_photos: bool = False,
                           progress_callback: Optional[Callable] = None,
                           min_id: Optional[int] = None,
                           batch_size: Optional[int] = None,
                           batch_callback: Optional[Callable] = None,
                           batch_delay: float = 0.0,
                           rate_limit_strategy: str = 'wait',
                           allow_full_fetch: bool = False,
                           download_media_to: Optional[str] = None,
                           include_media: bool = False) -> pd.DataFrame:
        """
        Fetch messages from a group with various filters.

        Rate-limit (FloodWait) interruptions are waited out and the fetch
        RESUMES from the last handled message — progress, batches, and
        settings are preserved. After MAX_FLOOD_RETRIES interruptions the
        fetch stops with a clear RuntimeError (including the resume cursor).

        Args:
            group_id: Telegram group/channel ID or username (e.g., '@channelname')
            limit: Maximum number of messages to fetch
            start_date: Get messages after this date (naive datetimes are treated as UTC)
            end_date: Get messages before this date (naive datetimes are treated as UTC)
            include_profile_photos: Whether to download profile photos
            progress_callback: Optional callback for progress updates
            min_id: Minimum message ID (for resuming)
            batch_size: If specified, process messages in batches of this size
            batch_callback: Optional async callback called for each batch (batch_df, batch_info)
            batch_delay: Delay in seconds between batches to avoid rate limits (default: 0)
            rate_limit_strategy: How to handle rate limits - 'wait' or 'exponential' (default: 'wait')
            allow_full_fetch: With no limit given, permit fetching past the
                DEFAULT_FETCH_LIMIT (750) safety bound (default: False)
            download_media_to: If set to a directory path, each message's own
                media (photos/videos/...) is downloaded there during the fetch
                and its path recorded in the MediaPath column (default: None =
                references only, no download)
            include_media: If True, each message's media is loaded in-memory as
                raw bytes into the MediaData column (mirrors include_profile_photos).
                Convenient for small scrapes; holds every file in RAM (default: False)

        Returns:
            DataFrame with messages
        """
        # Telegram message dates are UTC-aware; treat naive inputs as UTC
        # (Telethon's own convention for offset_date)
        start_date = self._ensure_utc(start_date)
        end_date = self._ensure_utc(end_date)

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
        iterated_count = 0
        batch_count = 0

        # Set up batching if requested
        batch_messages = []
        effective_batch_size = batch_size if batch_size and batch_callback else None

        # Prepare the media output directory once (download-during-fetch mode)
        if download_media_to:
            os.makedirs(download_media_to, exist_ok=True)

        # Resolve the effective limit: an explicit limit is always honored;
        # with none given, the safety bound applies unless allow_full_fetch
        safety_capped = limit is None and not allow_full_fetch
        effective_limit = DEFAULT_FETCH_LIMIT if safety_capped else limit

        # Bounded, resumable retry state for rate-limit interruptions
        flood_attempts = 0
        total_flood_wait = 0.0
        last_seen_id: Optional[int] = None  # last message fully handled (resume cursor)
        client = None

        while True:
            try:
                async with self.connection_engine.session() as client:
                    # Get the entity
                    channel = await client.get_entity(group_id)
                    logger.info(f"Fetching messages from: {channel.title}")

                    # Per-chat context stamped onto every row (provenance / deep links)
                    chat_id = channel.id
                    link_base = self._link_base(channel)

                    # Determine iteration parameters.
                    # Telethon: with reverse=True the offset is the ASCENDING start
                    # point (messages *after* it are returned); with reverse=False it
                    # is the newest bound (messages *before* it are returned).
                    if start_date:
                        # Forward walk (oldest→newest) from the window start.
                        # Pad 1s because Telethon's offset is exclusive; the in-loop
                        # filter below drops anything still before start_date.
                        offset_date = start_date - timedelta(seconds=1)
                        reverse = True
                    else:
                        # Backward walk (newest→oldest) from end_date, or from the
                        # newest message when unset (None = Telethon's default)
                        offset_date = end_date
                        reverse = False

                    iter_kwargs = {
                        'entity': channel,
                        'limit': effective_limit,  # None = full history (Telethon supports it)
                        'offset_date': offset_date,
                        'reverse': reverse
                    }

                    # Only add min_id if it's not None
                    if min_id is not None:
                        # Telethon's min_id is EXCLUSIVE: only ids strictly greater
                        # than it are returned (verified against Telethon 1.40)
                        iter_kwargs['min_id'] = min_id
                        # When using min_id (for polling), we want chronological order
                        iter_kwargs['reverse'] = True
                        reverse = True  # keep the local in sync for the loop's date filters
                        # Remove offset_date when using min_id to avoid conflicts
                        iter_kwargs.pop('offset_date', None)
                        logger.info(f"Polling with min_id={min_id}, limit={iter_kwargs.get('limit', 'no limit')}")

                    # Seatbelt: the cursor itself — Telethon should never return
                    # ids <= min_id, but skip any that would slip through
                    original_min_id = min_id if min_id else None

                    # Resume after a rate-limit interruption: continue from the
                    # last handled message instead of restarting from scratch
                    if last_seen_id is not None:
                        if iter_kwargs.get('reverse'):
                            iter_kwargs['min_id'] = max(iter_kwargs.get('min_id') or 0, last_seen_id)
                        else:
                            iter_kwargs['max_id'] = last_seen_id
                        iter_kwargs.pop('offset_date', None)
                        logger.info(f"Resuming fetch after message id {last_seen_id}")
                    if effective_limit is not None:
                        remaining = effective_limit - iterated_count
                        if remaining <= 0:
                            break  # the interruption hit at the very end — nothing left
                        iter_kwargs['limit'] = remaining

                    # Iterate through messages
                    async for msg in client.iter_messages(**iter_kwargs):
                        # NOTE: iterated_count ticks only when a message is fully
                        # HANDLED (same moments the resume cursor advances) — an
                        # interrupted message is re-fetched on resume and must not
                        # be double-counted against the limit.

                        # Skip messages we've already seen (when polling)
                        if original_min_id is not None and msg.id <= original_min_id:
                            logger.debug(f"Skipping already-seen message {msg.id} <= {original_min_id}")
                            last_seen_id = msg.id if last_seen_id is None else max(last_seen_id, msg.id)
                            iterated_count += 1
                            continue

                        if min_id is not None:
                            logger.debug(f"Processing message {msg.id} (min_id={min_id})")

                        # Apply date filters (direction-aware: stop as soon as the
                        # iteration order guarantees no further in-window messages)
                        if start_date and msg.date < start_date:
                            if reverse:
                                last_seen_id = msg.id  # 1s boundary pad: handled, window starts next
                                iterated_count += 1
                                continue
                            break  # descending: older than the window start — done
                        if end_date and msg.date > end_date:
                            if reverse:
                                break  # ascending: past the window end — done
                            last_seen_id = msg.id  # descending: newer than the window — handled
                            iterated_count += 1
                            continue

                        # Process message
                        message_data = await self._process_message(
                            msg,
                            client,
                            include_profile_photos,
                            chat_id=chat_id,
                            link_base=link_base,
                            media_dir=download_media_to,
                            include_media=include_media
                        )

                        if message_data:
                            messages_data.append(message_data.to_dict())

                            # Handle batch processing
                            if effective_batch_size:
                                batch_messages.append(message_data.to_dict())

                                # Process batch when it reaches the size
                                if len(batch_messages) >= effective_batch_size:
                                    batch_count += 1
                                    batch_df = self._to_frame(batch_messages)
                                    batch_info = {
                                        'batch_num': batch_count,
                                        'batch_size': len(batch_messages),
                                        'total_processed': processed_count + len(batch_messages),
                                        'group_id': group_id
                                    }

                                    # Call the batch callback
                                    await batch_callback(batch_df, batch_info)

                                    # Clear batch buffer
                                    batch_messages = []

                                    # Apply batch delay to avoid rate limits
                                    if batch_delay > 0:
                                        logger.info(f"Waiting {batch_delay}s between batches to avoid rate limits...")
                                        await asyncio.sleep(batch_delay)

                            processed_count += 1

                            # Update progress
                            if progress_tracker:
                                progress_tracker.update()

                            # Log progress
                            if processed_count % 100 == 0:
                                logger.info(f"Processed {processed_count} messages...")

                        # This message is fully handled — count it and advance the resume cursor
                        iterated_count += 1
                        last_seen_id = msg.id

                    # Process final batch if there are remaining messages
                    if effective_batch_size and batch_messages:
                        batch_count += 1
                        batch_df = self._to_frame(batch_messages)
                        batch_info = {
                            'batch_num': batch_count,
                            'batch_size': len(batch_messages),
                            'total_processed': processed_count,
                            'group_id': group_id,
                            'is_final': True
                        }
                        await batch_callback(batch_df, batch_info)

                    # Announce the safety bound whenever it actually truncated the fetch
                    if safety_capped and iterated_count >= DEFAULT_FETCH_LIMIT:
                        logger.warning(
                            f"Fetch for group {group_id} stopped at the {DEFAULT_FETCH_LIMIT}-message "
                            f"safety limit; more messages likely remain. Pass an explicit limit=... "
                            f"or allow_full_fetch=True to fetch more."
                        )

                break  # fetch completed

            except FloodWaitError as e:
                flood_attempts += 1
                total_flood_wait += e.seconds
                if flood_attempts > MAX_FLOOD_RETRIES:
                    msg_txt = (
                        f"Giving up after {flood_attempts} rate-limit interruptions "
                        f"(~{total_flood_wait:.0f}s of mandated waiting); {processed_count} messages "
                        f"fetched. Resume later with after_id={last_seen_id}."
                    )
                    logger.error(msg_txt)
                    raise RuntimeError(msg_txt) from e
                logger.warning(
                    f"FloodWait #{flood_attempts}/{MAX_FLOOD_RETRIES}: waiting {e.seconds}s, "
                    f"then resuming after message id {last_seen_id}"
                )
                await self.connection_engine.handle_rate_limit(e, client, strategy=rate_limit_strategy)
                # loop continues → resume from last_seen_id with identical settings

            except Exception as e:
                logger.error(f"Error fetching messages: {e}")
                raise

        # Create DataFrame
        df = self._to_frame(messages_data)

        # Sort by MessageId when using min_id (for polling)
        if min_id is not None and not df.empty:
            df = df.sort_values('MessageId', ascending=True)

        logger.info(f"Retrieved {len(df)} messages")

        # Heads-up on how much media is being held in RAM (include_media has no cap)
        if include_media and not df.empty and 'MediaData' in df.columns:
            total = int(df['MediaData'].dropna().apply(len).sum())
            logger.info(f"include_media: loaded {total / 1024 / 1024:.1f} MB of media into the DataFrame")
            if total > 250 * 1024 * 1024:
                logger.warning(
                    "include_media is holding >250 MB in memory; for larger scrapes prefer "
                    "download_media_to=<dir> (files on disk) or a smaller limit/date range."
                )

        return df

    @staticmethod
    def _ensure_utc(dt: Optional[datetime]) -> Optional[datetime]:
        """Make a datetime timezone-aware (naive = UTC, matching Telethon's convention)."""
        if dt is not None and dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt

    @staticmethod
    def _to_frame(records) -> pd.DataFrame:
        """Build a messages DataFrame from row dicts."""
        df = pd.DataFrame(records)
        if not df.empty:
            # Nullable int: NaN would force float64, which cannot represent
            # album ids (> 2^53) exactly and would corrupt GroupedId values
            df['GroupedId'] = df['GroupedId'].astype('Int64')
        return df

    @staticmethod
    def _link_base(chat) -> Optional[str]:
        """Base t.me URL for deep links to this chat's messages (None if not linkable)."""
        username = getattr(chat, 'username', None)
        if username:
            return f"https://t.me/{username}"
        if isinstance(chat, tl_types.Channel):
            # private channels/megagroups use the internal-id link form
            return f"https://t.me/c/{chat.id}"
        return None  # basic (legacy) groups have no message links

    @staticmethod
    def _detect_media_type(msg) -> Optional[str]:
        """Classify a message's attachment ('photo', 'video', ...); None for text-only."""
        media = msg.media
        if media is None:
            return None
        if isinstance(media, tl_types.MessageMediaPhoto):
            return 'photo'
        if isinstance(media, tl_types.MessageMediaDocument):
            if msg.sticker:
                return 'sticker'
            if msg.gif:
                return 'gif'
            if msg.video_note:
                return 'video_note'
            if msg.video:
                return 'video'
            if msg.voice:
                return 'voice'
            if msg.audio:
                return 'audio'
            return 'document'
        if isinstance(media, tl_types.MessageMediaWebPage):
            return 'webpage'  # link preview, not an attachment
        if isinstance(media, tl_types.MessageMediaContact):
            return 'contact'
        if isinstance(media, (tl_types.MessageMediaGeo, tl_types.MessageMediaGeoLive, tl_types.MessageMediaVenue)):
            return 'geo'
        if isinstance(media, tl_types.MessageMediaPoll):
            return 'poll'
        return 'other'

    @staticmethod
    def _media_stem(chat_id: Optional[int], message_id: int) -> str:
        """
        Deterministic, self-identifying filename stem for a message's media:
        '<chat_id>_<message_id>' (falls back to just the message id if chat_id is
        unknown). Passed WITHOUT an extension — Telethon appends the correct one
        (.jpg/.mp4/...). This makes each file traceable to its exact message/group
        from the filename alone, and unique across groups sharing one folder.
        """
        return f"{chat_id}_{message_id}" if chat_id is not None else str(message_id)

    async def _download_or_reuse(self, client, msg, media_dir: str, chat_id: Optional[int]):
        """
        Download a message's media to '<media_dir>/<chat_id>_<message_id>.<ext>',
        REUSING the file if it already exists (idempotent re-scrape).

        The extension is predicted up-front with telethon.utils.get_extension (an
        O(1) exists-check, no directory scan), so re-scraping an overlapping range
        neither re-downloads the bytes nor produces Telethon's ' (1)' duplicates —
        each message maps to exactly one file, forever.
        """
        stem = self._media_stem(chat_id, msg.id)
        ext = tl_utils.get_extension(msg.media) or ''
        target = os.path.join(media_dir, stem + ext)
        if ext and os.path.exists(target):
            logger.debug(f"Media for message {msg.id} already present ({stem}{ext}); reusing")
            return target
        # File doesn't exist yet: Telethon writes exactly to `target` (no rename).
        return await client.download_media(msg, file=target)

    async def _process_message(self,
                             msg,
                             client,
                             include_profile_photos: bool,
                             chat_id: Optional[int] = None,
                             link_base: Optional[str] = None,
                             media_dir: Optional[str] = None,
                             include_media: bool = False) -> Optional[MessageData]:
        """Process a single message"""
        try:
            sender = await msg.get_sender()
            if not sender:
                return None

            # Extract sender info
            sender_name = f"{getattr(sender, 'first_name', '') or ''} {getattr(sender, 'last_name', '') or ''}".strip()
            # None (not a sentinel string) when the sender has no public @username
            username = f"@{sender.username}" if hasattr(sender, 'username') and sender.username else None

            # Create message data
            message_data = MessageData(
                message_id=msg.id,
                sender_id=sender.id,
                sender_name=sender_name,
                username=username,
                message=msg.message,
                date=msg.date,
                reply_to_id=msg.reply_to_msg_id,
                forwarded_from=msg.fwd_from.from_id if msg.fwd_from else None,
                chat_id=chat_id,
                media_type=MessageEngine._detect_media_type(msg),
                grouped_id=msg.grouped_id,
                message_link=f"{link_base}/{msg.id}" if link_base else None
            )

            # Download profile photo if requested
            if include_profile_photos and hasattr(sender, 'photo') and sender.photo:
                try:
                    photo_bytes = await client.download_profile_photo(sender, file=bytes)
                    message_data.photo_data = photo_bytes
                except Exception as e:
                    logger.warning(f"Failed to download photo for {sender.id}: {e}")

            # Download the message's own media (photos/videos/...) if requested.
            # download_media returns the saved path, or None for nothing-to-download
            # (e.g. text-only or a link-preview webpage).
            if media_dir and msg.media is not None:
                try:
                    message_data.media_path = await self._download_or_reuse(
                        client, msg, media_dir, chat_id
                    )
                except Exception as e:
                    logger.warning(f"Failed to download media for message {msg.id}: {e}")

            # Load the message's media in-memory as raw bytes if requested
            # (None for nothing-to-download, e.g. a link-preview webpage).
            if include_media and msg.media is not None:
                try:
                    message_data.media_data = await client.download_media(msg, file=bytes)
                except Exception as e:
                    logger.warning(f"Failed to load media bytes for message {msg.id}: {e}")

            return message_data

        except Exception as e:
            logger.error(f"Error processing message {msg.id}: {e}")
            return None



    async def download_media_by_id(self,
                             group_id: Union[int, str],
                             message_ids: Union[int, Iterable[int]],
                             output_dir: Optional[str] = None) -> Dict[int, Any]:
        """
        Download the media attached to specific messages, on demand.

        This is the counterpart to the reference columns from fetch: get_messages
        returns MediaType/GroupedId/ChatId/MessageId cheaply; call this later to
        pull the actual bytes only for the messages you decide to keep (matches
        "host photos only as needed; don't bulk-mirror"). It re-fetches the raw
        Telethon message by id — the object the fetch path doesn't expose.

        For an album (multi-photo post), pass every MessageId sharing a GroupedId.

        Args:
            group_id: Telegram group/channel id or '@username'
            message_ids: a single message id, or an iterable of ids
            output_dir: directory to save files into (created if missing).
                If None, returns raw bytes instead of writing files.

        Returns:
            {message_id: filepath (str) | bytes | None}
            None means the message has no downloadable media (text-only, or a
            link-preview 'webpage' with no file).
        """
        ids = [message_ids] if isinstance(message_ids, int) else list(message_ids)
        if not ids:
            return {}

        results: Dict[int, Any] = {}
        try:
            async with self.connection_engine.session() as client:
                entity = await client.get_entity(group_id)
                # get_messages(ids=...) returns entries positionally aligned to
                # `ids`, with None for any id that no longer exists
                msgs = await client.get_messages(entity, ids=ids)
                if output_dir:
                    os.makedirs(output_dir, exist_ok=True)

                for mid, msg in zip(ids, msgs):
                    if msg is None or msg.media is None:
                        results[mid] = None
                        continue
                    try:
                        if output_dir:
                            # Named '<chat_id>_<message_id>.<ext>', reused if already present
                            results[mid] = await self._download_or_reuse(
                                client, msg, output_dir, entity.id
                            )
                        else:
                            # In-memory bytes when no output_dir was given
                            results[mid] = await client.download_media(msg, file=bytes)
                    except Exception as e:
                        logger.warning(f"Failed to download media for message {mid}: {e}")
                        results[mid] = None

            got = sum(1 for v in results.values() if v is not None)
            logger.info(f"Downloaded media for {got}/{len(ids)} messages from {group_id}")
            return results

        except Exception as e:
            logger.error(f"Error downloading media: {e}")
            raise

    async def get_message_count(self, group_id: int) -> int:
        """
        Get total message count for a group.

        Args:
            group_id: Telegram group/channel ID or username (e.g., '@channelname')

        Returns:
            Total message count
        """
        try:
            async with self.connection_engine.session() as client:
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
            group_id: Telegram group/channel ID or username (e.g., '@channelname')
            query: Search query
            limit: Maximum number of results

        Returns:
            DataFrame with matching messages
        """
        try:
            messages_data = []

            async with self.connection_engine.session() as client:
                channel = await client.get_entity(group_id)
                chat_id = channel.id
                link_base = self._link_base(channel)

                async for msg in client.iter_messages(
                    channel,
                    search=query,
                    limit=limit
                ):
                    message_data = await self._process_message(
                        msg, client, False, chat_id=chat_id, link_base=link_base
                    )
                    if message_data:
                        messages_data.append(message_data.to_dict())

            df = self._to_frame(messages_data)
            logger.info(f"Found {len(df)} messages matching '{query}'")
            return df

        except Exception as e:
            logger.error(f"Error searching messages: {e}")
            raise
