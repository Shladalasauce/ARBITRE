class LiveExecutor:
    """Safety boundary: live routing is intentionally unavailable in this release."""
    async def execute(self, _opportunity):
        raise PermissionError("Live trading is disabled. This build supports read-only scanning and paper execution only.")

