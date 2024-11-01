class ContextError(Exception):
    pass


class ContextNotFound(ContextError):
    pass


class ContextNotConfigured(ContextError):
    pass
