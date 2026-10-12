"""Names used by the preserved r3 probes; runtime comes from the new export."""
from contextlib import contextmanager
from tgdata.account_pool import AccountPool as CandidatePool
from tgdata.pool_state import _SourceInterrupted
from tgdata.pool_lifecycle import _SCOPES
from tgdata.pool_observation import MAX_EVENTS, MAX_EVENT_BYTES, MAX_TOTAL_BYTES, MAX_DROPPED

@contextmanager
def install(test_module):
    assert test_module.AccountPool is CandidatePool
    yield
