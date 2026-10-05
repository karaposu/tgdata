"""Bounded raw-message preparation through tgdata's existing guarded client."""

from datetime import datetime, timezone
import operator
import os

from telethon import utils as tl_utils
from telethon.tl import types

from .batch_files import download_blob, prepare_directory
from .message_batch import (
    BatchFormatError, MessageBatch, MAX_BATCH_MESSAGES, MAX_MESSAGE_ID, MAX_LONG,
    MIN_LONG, _identifier, _validate_record,
)
from .message_engine import GroupAccessError, MessageEngine


def _integer(value, name, minimum, maximum):
    try:
        if isinstance(value, bool):
            raise TypeError
        number = int(operator.index(value))
        if not minimum <= number <= maximum:
            raise ValueError
        return number
    except (TypeError, ValueError, OverflowError):
        raise BatchFormatError('{} must be an integer from {} to {}'.format(name, minimum, maximum)) from None


def _group_argument(value):
    if isinstance(value, str):
        value = value.strip()
        if not value:
            raise BatchFormatError('an explicit group ID or name is required')
        if not value.lstrip('-').isdigit():
            return value
        try:
            value = int(value)
        except ValueError:
            raise BatchFormatError('group ID is outside its integer range') from None
    value = _integer(value, 'group_id', MIN_LONG, MAX_LONG)
    if value == 0:
        raise BatchFormatError('group_id must not be zero')
    return value


def _id_text(value):
    if value is None:
        return None
    return str(_integer(value, 'message identifier', MIN_LONG, MAX_LONG))


def _peer_text(peer):
    return str(tl_utils.get_peer_id(peer)) if peer is not None else None


def _timestamp(value):
    if value is None:
        return None
    if not isinstance(value, datetime):
        raise BatchFormatError('message date must be a datetime or absent')
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat(timespec='microseconds').replace('+00:00', 'Z')


def _sender(message):
    # Use the wire peer, not an SDK-inferred self ID from a possibly stale
    # cache. Missing authors remain null; no enrichment request is sent.
    ident = _peer_text(getattr(message, 'from_id', None))
    result = {'id': ident, 'name': None, 'username': None}
    if ident is None:
        return result
    sender = message.sender
    if sender is None or _peer_text(sender) != ident:
        return result
    if isinstance(sender, types.User):
        name = ' '.join(part for part in (sender.first_name, sender.last_name) if part)
    else:
        name = getattr(sender, 'title', None)
    result['name'] = name or None
    result['username'] = getattr(sender, 'username', None)
    return result


def _photo_size(client, photo):
    # Match the SDK's selected representation, including cached/progressive
    # sizes. A photo without a usable size can still be a raw reference.
    try:
        selected = client._get_thumb(photo.sizes + (photo.video_sizes or []), None)
    except (ValueError, IndexError):
        return None
    if isinstance(selected, types.PhotoStrippedSize):
        return len(tl_utils.stripped_photo_to_jpg(selected.bytes))
    if isinstance(selected, types.PhotoCachedSize):
        return len(selected.bytes)
    if isinstance(selected, types.PhotoSizeProgressive):
        return max(selected.sizes)
    return getattr(selected, 'size', None)


def _media(message, client):
    raw = message.media
    if raw is None or isinstance(raw, types.MessageMediaEmpty):
        return None
    result = {
        'kind': MessageEngine._detect_media_type(message), 'id': None,
        'mime_type': None, 'file_name': None, 'size': None,
        'downloadable': False, 'blob': None,
    }
    if isinstance(raw, types.MessageMediaPhoto):
        asset = raw.photo
        result['id'] = _id_text(getattr(asset, 'id', None) or None)
        if isinstance(asset, types.Photo):
            result['downloadable'] = True
            result['size'] = _photo_size(client, asset)
    elif isinstance(raw, types.MessageMediaDocument):
        asset = raw.document
        result['id'] = _id_text(getattr(asset, 'id', None) or None)
        if isinstance(asset, types.Document):
            result['downloadable'] = True
            result['mime_type'] = asset.mime_type
            result['size'] = asset.size
            result['file_name'] = next((a.file_name for a in asset.attributes
                                        if isinstance(a, types.DocumentAttributeFilename)), None)
    return result


def _record(message, client):
    action = getattr(message, 'action', None)
    forward = getattr(message, 'fwd_from', None)
    return {
        'id': _id_text(message.id), 'kind': 'service' if action is not None else 'message',
        'date': _timestamp(message.date), 'edit_date': _timestamp(getattr(message, 'edit_date', None)),
        'text': message.message, 'sender': _sender(message),
        'post_author': getattr(message, 'post_author', None),
        'reply_to_id': _id_text(message.reply_to_msg_id),
        'forward_from_id': _peer_text(getattr(forward, 'from_id', None)),
        'grouped_id': _id_text(message.grouped_id),
        'service_action': type(action).__name__ if action is not None else None,
        'media': _media(message, client),
    }


class BatchEngine:
    def __init__(self, connection_engine):
        self.connection_engine = connection_engine

    async def fetch_batch(self, group_id, *, after_id=0, limit=200, download_media_to=None):
        group_id = _group_argument(group_id)
        after_id = _integer(after_id, 'after_id', 0, MAX_MESSAGE_ID)
        limit = _integer(limit, 'limit', 1, MAX_BATCH_MESSAGES)
        media_directory = None
        if download_media_to is not None:
            if not isinstance(download_media_to, (str, os.PathLike)) or download_media_to == '':
                raise BatchFormatError('download_media_to must be an explicit directory path')
            media_directory = prepare_directory(download_media_to)
        mode = 'download' if media_directory is not None else 'references'
        chat_id = None
        records = []
        last_id = after_id
        try:
            async with self.connection_engine.session() as client:
                try:
                    entity = await client.get_entity(group_id)
                except ValueError:
                    entity = await MessageEngine._entity_after_dialog_sync(client, group_id)
                if isinstance(entity, (types.ChatForbidden, types.ChannelForbidden)):
                    raise GroupAccessError('account has no access to the requested group')
                if not isinstance(entity, (types.Chat, types.Channel)):
                    raise BatchFormatError('group_id must resolve to a group or channel')
                resolved_id = tl_utils.get_peer_id(entity)
                _identifier(str(resolved_id), 'chat_id', MIN_LONG, -1)
                chat_id = resolved_id
                if after_id == MAX_MESSAGE_ID:
                    # No representable message ID can follow this cursor. The
                    # SDK's reverse iterator otherwise increments it past int32.
                    return MessageBatch._from_records(chat_id, after_id, records, mode, 'end')

                async for message in client.iter_messages(entity, min_id=after_id, reverse=True, limit=limit):
                    if tl_utils.get_peer_id(message.peer_id) != chat_id:
                        raise BatchFormatError('message belongs to a different chat')
                    record = _record(message, client)
                    ident = _validate_record(record, 'references')
                    if ident <= last_id:
                        raise BatchFormatError('message IDs did not advance after the cursor')
                    media = record['media']
                    if media_directory is not None and media is not None and media['downloadable']:
                        async def writer(output):
                            return await client.download_media(message, file=output)

                        media['blob'] = await download_blob(media_directory, writer, expected_size=media['size'])
                    _validate_record(record, mode)
                    records.append(record)
                    last_id = ident
            reason = 'limit' if len(records) == limit else 'end'
            return MessageBatch._from_records(chat_id, after_id, records, mode, reason)
        except Exception as error:
            if chat_id is not None:
                error.partial_result = MessageBatch._from_records(chat_id, after_id, records, mode, 'interrupted')
            raise
