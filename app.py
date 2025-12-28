import time
import tomllib
from pathlib import Path

import requests
from flask import Flask, jsonify, render_template

app = Flask(__name__)

CONFIG_PATH = Path(__file__).parent / "config.toml"
LOCAL_CONFIG_PATH = Path(__file__).parent / "config.local.toml"


def deep_merge(base: dict, override: dict) -> dict:
    """Deep merge override into base, returning a new dict."""
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def load_config():
    """Load configuration from config.toml, with config.local.toml overrides."""
    with open(CONFIG_PATH, "rb") as f:
        config = tomllib.load(f)

    if LOCAL_CONFIG_PATH.exists():
        with open(LOCAL_CONFIG_PATH, "rb") as f:
            local_config = tomllib.load(f)
        config = deep_merge(config, local_config)

    return config


@app.route("/")
def index():
    """Render the dashboard."""
    config = load_config()
    return render_template("index.html", services=config.get("services", {}))


@app.route("/health/<service_id>")
def health_check(service_id):
    """Check if a service is reachable."""
    services = load_config().get("services", {})

    if service_id not in services:
        return jsonify({"status": "unknown", "error": "Service not found"}), 404

    service = services[service_id]
    url = service.get("url", "")

    try:
        start = time.time()
        response = requests.get(url, timeout=5)
        latency_ms = int((time.time() - start) * 1000)

        if response.status_code < 500:
            return jsonify({"status": "up", "latency_ms": latency_ms})
        else:
            return jsonify({"status": "down", "latency_ms": latency_ms})

    except requests.RequestException:
        return jsonify({"status": "down", "latency_ms": None})


def main():
    """Entry point for the application."""
    config = load_config()
    port = config.get("server", {}).get("port", 5000)
    app.run(debug=True, host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()
