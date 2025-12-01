import argparse
import os
import time
import csv
import threading
import Pyro5.api
import Pyro5.server

from coordinator import Coordinator
from node import URLNode


def write_crawled_urls_to_csv(data: list[dict], filename: str) -> None:
    """Write crawled URL data to a CSV file."""
    if not data:
        print("No data to write to CSV.")
        return

    keys = data[0].keys()
    with open(filename, mode="w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=keys)
        writer.writeheader()
        writer.writerows(data)
    print(f"Crawled URLs saved to '{filename}'")


def write_stats_to_txt(urls: list[str], node_count: int, edge_count: int, filename: str) -> None:
    """Write crawl statistics to a text file."""
    with open(filename, mode="w", encoding="utf-8") as file:
        file.write(f"Total pages discovered: {node_count}\n")
        file.write(f"Total pages visited: {node_count}\n")
        file.write(f"Total links found: {edge_count}\n")
        file.write("\nVisited URLs:\n")

        for url in urls:
            file.write(f"- {url}\n")

    print(f"Stats written to '{filename}'")


def main():
    parser = argparse.ArgumentParser(description="Distributed Web Crawler - Coordinator Server")
    parser.add_argument("--run_minutes", "-t", help="Crawl duration in minutes.", type=float, default=1.0)
    parser.add_argument("--url", "-u", help="Starting URL to crawl.", type=str, default="http://www.dlsu.edu.ph")
    parser.add_argument("--host", "-H", help="Host to bind the server to.", type=str, default="localhost")
    parser.add_argument("--port", "-p", help="Port to bind the server to.", type=int, default=9999)
    parser.add_argument("--output", "-o", help="Output directory for results.", type=str, default=".")
    args = parser.parse_args()

    os.makedirs(args.output, exist_ok=True)

    seed_url = URLNode(args.url).url

    print(f"Starting coordinator server for crawl of {seed_url}")
    print(f"Crawl duration: {args.run_minutes} minutes")
    print(f"Server: {args.host}:{args.port}")

    coordinator = Coordinator(seed_url)

    # Create Pyro daemon
    daemon = Pyro5.server.Daemon(host=args.host, port=args.port)
    uri = daemon.register(coordinator, "crawler.coordinator")

    print(f"\nCoordinator URI: {uri}")
    print("Waiting for workers to connect...")
    print("(Start workers with: python run_client.py)\n")

    # Run daemon in a separate thread
    daemon_thread = threading.Thread(target=daemon.requestLoop)
    daemon_thread.daemon = True
    daemon_thread.start()

    # Wait for crawl duration
    crawl_duration_seconds = args.run_minutes * 60
    start_time = time.time()

    try:
        while time.time() - start_time < crawl_duration_seconds:
            stats = coordinator.get_stats()
            elapsed = time.time() - start_time
            print(
                f"\r[{elapsed:.1f}s] Queue: {stats['queue_size']}, "
                f"Visited: {stats['visited_count']}, "
                f"Data: {stats['data_count']}",
                end="",
                flush=True,
            )
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\nCaught KeyboardInterrupt, stopping crawl...")

    print(f"\n\nTime limit reached ({args.run_minutes} minutes). Stopping...")

    coordinator.stop()

    time.sleep(2)

    # Get final results
    data, urls, node_count, edge_count = coordinator.get_results()

    # Write output files
    graph_file = os.path.join(args.output, "dlsu_crawl.graphml")
    csv_file = os.path.join(args.output, "crawled_urls.csv")
    stats_file = os.path.join(args.output, "metadata.txt")

    coordinator.export_graph(graph_file)
    print(f"Graph saved as '{graph_file}'")

    write_crawled_urls_to_csv(data, csv_file)
    write_stats_to_txt(urls, node_count, edge_count, stats_file)

    end_time = time.time()
    print(f"\nCrawl complete in {end_time - start_time:.2f} seconds.")
    print(f"Total pages visited: {node_count}")
    print(f"Total links found: {edge_count}")

    daemon.shutdown()


if __name__ == "__main__":
    main()
