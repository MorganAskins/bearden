"""Gunicorn configuration file for bearden dashboard."""

import tomllib
from pathlib import Path


def _load_port() -> int:
    """Load port from config files."""
    config_path = Path(__file__).parent / "config.toml"
    local_config_path = Path(__file__).parent / "config.local.toml"

    port = 5000
    if config_path.exists():
        with open(config_path, "rb") as f:
            app_config = tomllib.load(f)
            port = app_config.get("server", {}).get("port", port)

    if local_config_path.exists():
        with open(local_config_path, "rb") as f:
            local_app_config = tomllib.load(f)
            port = local_app_config.get("server", {}).get("port", port)

    return port


_port = _load_port()

# Server socket
bind = f"0.0.0.0:{_port}"

# Worker processes
workers = 2

# Timeout for graceful worker restart
graceful_timeout = 30

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"

# Process naming
proc_name = "bearden"
