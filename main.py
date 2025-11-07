import threading
import time
import networkx as nx
from queue import Queue
import argparse
import csv

from node import URLNode
from worker import worker

def write_crawled_urls_to_csv(crawled_urls_data, filename="crawled_urls.csv"):
    """Writes the final scraped data to a CSV file."""
    if not crawled_urls_data:
        print("No data to write to CSV.")
        return
        
    keys = crawled_urls_data[0].keys()
    with open(filename, mode='w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=keys)
        writer.writeheader()
        writer.writerows(crawled_urls_data)
    print(f"Crawled URLs saved to '{filename}'")

def write_stats_to_txt(graph, filename="metadata.txt"):
    """Writes the crawl statistics to a text file."""
    num_discovered_pages = graph.number_of_nodes()
    num_visited_pages = num_discovered_pages 
    num_links = graph.number_of_edges()

    with open(filename, mode='w', encoding='utf-8') as file:
        file.write(f"Total pages discovered: {num_discovered_pages}\n")
        file.write(f"Total pages visited: {num_visited_pages}\n")
        file.write(f"Total links found: {num_links}\n")
        file.write("\nVisited URLs:\n")

        for url in sorted(list(graph.nodes())):
            file.write(f"- {url}\n")

    print(f"Stats written to '{filename}'")

def main():
    parser = argparse.ArgumentParser(description="Parallel Web Scraper")
    parser.add_argument("--run_minutes", '-t', help="Specifies worker time.", type=float, default=1.0)
    parser.add_argument("--num_threads", '-n', help="Number of threads used for scraping.", type=int, default=4)
    parser.add_argument("--url", '-u', help="Specifies URL to scrape.", type=str, default="http://www.dlsu.edu.ph")
    args = parser.parse_args()

    print(f"Starting crawl of {args.url} for {args.run_minutes} minutes with {args.num_threads} threads.")

    url_queue = Queue()
    visited = set()
    graph = nx.DiGraph()
    crawled_urls_data = [] 

    topology_lock = threading.Lock()
    data_lock = threading.Lock()
    stop_event = threading.Event()

    # --- Initialization ---
    start_node = URLNode(args.url)
    url_queue.put(start_node)
    visited.add(start_node.url)
    graph.add_node(start_node.url)

    # --- Start Worker Threads ---
    threads = []
    for _ in range(args.num_threads):
        thread = threading.Thread(
            target=worker,
            args=(
                url_queue,
                visited,
                graph,
                crawled_urls_data,
                topology_lock,
                data_lock,
                stop_event
            )
        )
        thread.start()
        threads.append(thread)

    crawl_duration_seconds = args.run_minutes * 60
    start_time = time.time()
    try:
        time.sleep(crawl_duration_seconds)
    except KeyboardInterrupt:
        print("\nCaught KeyboardInterrupt, stopping crawl...")
    
    print(f"\nTime limit reached ({args.run_minutes} minutes). Signaling threads to stop...")
    
    stop_event.set()

    # Wait for all threads to finish
    for thread in threads:
        thread.join()

    print("All threads have stopped.")
    end_time = time.time()
    
    # --- Write Results ---
    nx.write_graphml(graph, "dlsu_crawl.graphml")
    print("Graph saved as 'dlsu_crawl.graphml'")
    
    write_crawled_urls_to_csv(crawled_urls_data)
    write_stats_to_txt(graph)
    
    print(f"\nCrawl complete in {end_time - start_time:.2f} seconds.")
    print(f"Total pages visited: {graph.number_of_nodes()}")
    print(f"Total links found: {graph.number_of_edges()}")

if __name__ == "__main__":
    main()
