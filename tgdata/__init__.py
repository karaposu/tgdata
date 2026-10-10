"""
tgdata - Telegram Data Extraction Library

A production-grade Python library for extracting and processing Telegram group and channel messages.
"""

# Main class
from .tgdata import TgData

# Errors
from .message_engine import GroupAccessError
from .group_operations import (
    GroupMetadata, GroupLookup, GroupAccess, GroupReferenceError, GroupResponseError,
)
from .connection_engine import AuthRequiredError, ProxyConfigError
from .discovery_engine import DiscoveryInterrupted
from .message_batch import MessageBatch, BatchFormatError
from .batch_files import BatchStorageError
from .backfill import (
    BackfillRunRef, BackfillStartRequest, BackfillPrepareContext, BackfillDeliveryRef,
    BackfillStatus, BackfillStartResult, BackfillTurn, BackfillControlResult, BackfillRecoveryResult,
    BackfillError, BackfillConfigurationError, BackfillConflictError, BackfillUnknownRun,
    BackfillUnknownCommand, BackfillStateError, BackfillStorageError, BackfillUnknownReceipt,
    BackfillRecoveryRequired, BackfillMediaError, BackfillClockError,
)
from .sync_store import (
    SQLiteSyncStore, SyncStatus, SyncError, SyncConfigurationError,
    SyncNotInitializedError, SyncConflictError, SyncStorageError,
)
from .read_budget import (
    ReadBudget, ReadBudgetStatus, ReadBudgetError, ReadBudgetExceeded,
    ReadBudgetConfigError, ReadBudgetStorageError, UnsupportedBudgetRequest,
)

# Models
from .models import (
    MessageData,
    GroupInfo,
    ConnectionConfig,
    RateLimitInfo
)

# Utilities
from .utils import (
    format_message_for_display,
    export_to_json,
    export_to_csv,
    filter_messages_by_sender,
    filter_messages_by_content,
    get_message_statistics,
    save_profile_photos,
    create_metrics_report,
    build_search_queries
)

# Progress tracking
from .progress import ProgressTracker

__version__ = "0.0.8"

__all__ = [
    # Main class
    "TgData",

    # Errors
    "GroupAccessError",
    "GroupMetadata",
    "GroupLookup",
    "GroupAccess",
    "GroupReferenceError",
    "GroupResponseError",
    "AuthRequiredError",
    "ProxyConfigError",
    "DiscoveryInterrupted",
    "MessageBatch",
    "BatchFormatError",
    "BatchStorageError",
    "BackfillRunRef",
    "BackfillStartRequest",
    "BackfillPrepareContext",
    "BackfillDeliveryRef",
    "BackfillStatus",
    "BackfillStartResult",
    "BackfillTurn",
    "BackfillControlResult",
    "BackfillRecoveryResult",
    "BackfillError",
    "BackfillConfigurationError",
    "BackfillConflictError",
    "BackfillUnknownRun",
    "BackfillUnknownCommand",
    "BackfillStateError",
    "BackfillStorageError",
    "BackfillUnknownReceipt",
    "BackfillRecoveryRequired",
    "BackfillMediaError",
    "BackfillClockError",
    "SQLiteSyncStore",
    "SyncStatus",
    "SyncError",
    "SyncConfigurationError",
    "SyncNotInitializedError",
    "SyncConflictError",
    "SyncStorageError",
    "ReadBudget",
    "ReadBudgetStatus",
    "ReadBudgetError",
    "ReadBudgetExceeded",
    "ReadBudgetConfigError",
    "ReadBudgetStorageError",
    "UnsupportedBudgetRequest",

    # Models
    "MessageData",
    "GroupInfo",
    "ConnectionConfig",
    "RateLimitInfo",

    # Utilities
    "format_message_for_display",
    "export_to_json",
    "export_to_csv",
    "filter_messages_by_sender",
    "filter_messages_by_content",
    "get_message_statistics",
    "save_profile_photos",
    "create_metrics_report",
    "build_search_queries",

    # Progress
    "ProgressTracker"
]
