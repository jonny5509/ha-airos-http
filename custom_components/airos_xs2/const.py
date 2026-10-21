DOMAIN = "airos_xs2"
DEFAULT_SCAN_INTERVAL = 60


def device_identifier(host: str) -> str:
    """Return a transport-independent identifier for the same physical device."""
    return host.strip().removeprefix("http://").removeprefix("https://").rstrip("/").lower()
