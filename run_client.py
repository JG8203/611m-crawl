import argparse
import time
import Pyro5.api

from client import run_worker


def connect_with_retry(uri: str, max_retries: int = 10, delay: float = 2.0):
    """Try to connect to coordinator with retries."""
    for attempt in range(max_retries):
        try:
            coordinator = Pyro5.api.Proxy(uri)
            stats = coordinator.get_stats()
            return coordinator, stats
        except Pyro5.errors.CommunicationError:
            if attempt < max_retries - 1:
                print(f"Connection failed, retrying in {delay}s... ({attempt + 1}/{max_retries})")
                time.sleep(delay)
            else:
                raise


def main():
    parser = argparse.ArgumentParser(description="Distributed Web Crawler - Worker Client")
    parser.add_argument("--host", "-H", help="Coordinator server host.", type=str, default="localhost")
    parser.add_argument("--port", "-p", help="Coordinator server port.", type=int, default=9999)
    parser.add_argument("--delay", "-d", help="Startup delay in seconds.", type=float, default=0)
    args = parser.parse_args()

    # Startup delay
    if args.delay > 0:
        print(f"Waiting {args.delay}s before starting...", flush=True)
        time.sleep(args.delay)

    uri = f"PYRO:crawler.coordinator@{args.host}:{args.port}"

    print(f"Connecting to coordinator at {uri}", flush=True)

    try:
        coordinator, stats = connect_with_retry(uri)
        print(f"Connected! Current stats: {stats}")
        print("Starting worker...\n")

        run_worker(uri)

        print("\nWorker stopped.")

    except Pyro5.errors.CommunicationError as e:
        print(f"Failed to connect to coordinator: {e}")
        print("Make sure the server is running (python run_server.py)")


if __name__ == "__main__":
    main()
