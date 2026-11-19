#!/usr/bin/env python3
"""Start Tutti: `python3 run.py [--port 8000] [--reset]`."""
import argparse
import logging
import sys

from server.app import make_server
from server.db import SchemaOutOfDate
from server.config import Settings, log
from server.setup import prepare_data


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the Tutti investor demo.")
    parser.add_argument("--port", type=int, default=8000, help="port to listen on (default 8000)")
    parser.add_argument("--reset", action="store_true", help="wipe the database and uploads, then reseed")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    settings = Settings()
    try:
        prepare_data(settings, reset=args.reset)
        server = make_server(settings, args.port, host = "0.0.0.0")
    except SchemaOutOfDate as error:
        log.error("%s", error)
        return 1
    except OSError as error:
        log.error("Could not start on port %d: %s. Try another with --port.", args.port, error)
        return 1
    print("Tutti is running (Ctrl+C to stop)", args.port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        log.info("Stopping.")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
