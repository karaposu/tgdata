# Experiment-only function snapshot; globals come from the unchanged worker protocol module.
def describe_error(error):
    result = {'category': 'operation_error', 'type': error_type(error)}
    if isinstance(error, WorkerError):
        result.update(category='worker_error', code=error.code)
        if error.field is not None:
            result['field'] = error.field
    elif isinstance(error, AuthRequiredError):
        result['category'] = 'authentication_required'
        reason = _optional(lambda: error.reason)
        if type(reason) is str and reason in _CANONICAL_AUTH_REASONS:
            result['reason'] = reason
        for name in ('banned', 'first_login'):
            value = _optional(lambda: getattr(error, name))
            if type(value) is bool:
                result[name] = value
    elif isinstance(error, AccountIdentityError):
        result['category'] = 'identity_mismatch'
        for name in ('expected_account_id', 'actual_account_id'):
            value = _optional(lambda: getattr(error, name))
            if value is None or type(value) is int:
                result[name] = str(value) if value is not None else None
    elif isinstance(error, (ReadBudgetError, JoinBudgetError)):
        result['category'] = 'allowance_error'
        if isinstance(error, (ReadBudgetExceeded, JoinBudgetExceeded)):
            status = _optional(lambda: _plain(error.status.to_dict()))
            if status is not None:
                result['status'] = identifiers(status)
    elif isinstance(error, (GroupReferenceError, GroupResponseError, GroupAccessError)):
        result['category'] = 'group_error'
    elif isinstance(error, ProxyConfigError):
        result['category'] = 'configuration_error'
    elif isinstance(error, RPCError):
        result['category'] = 'telegram_error'
        # Named SDK classes have a bounded canonical name. Generic RPC .message
        # is intentionally not copied: it is arbitrary exception text.
        name = health._TELEGRAM_NAMES.get(type(error))
        if type(name) is str and _NAME.fullmatch(name):
            result['name'] = name
        code = _optional(lambda: error.code)
        if type(code) is int and -(1 << 31) <= code < (1 << 31):
            result['code'] = code
        seconds = _optional(lambda: error.seconds)
        if type(seconds) is int and 0 <= seconds <= MAX_LONG:
            result['wait_seconds'] = seconds
    return result
