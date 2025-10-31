from node import URLNode
from bfs import bfs
import threading
from queue import Queue
import networkx as nx
from url_processor import url_processor_worker
import csv
import argparse

def write_crawled_urls_to_csv(crawled_urls_data, filename="crawled_urls.csv"):
    keys = crawled_urls_data[0].keys() if crawled_urls_data else []
    with open(filename, mode='w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=keys)
        writer.writeheader()
        writer.writerows(crawled_urls_data)

def write_stats_to_txt(graph, visited_urls, filename="metadata.txt"):
    num_discovered_pages = graph.number_of_nodes()
    num_visited_pages = len(visited_urls)
    num_links = graph.number_of_edges()

    with open(filename, mode='w', encoding='utf-8') as file:
        file.write(f"Total pages discovered: {num_discovered_pages}\n")
        file.write(f"Total pages visited: {num_visited_pages}\n")
        file.write(f"Total links found: {num_links}\n")
        file.write("\nVisited URLs:\n")

        for url in visited_urls:
            file.write(f"- {url}\n")

    print(f"Stats written to '{filename}'")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run_minutes", '-t', help="Specifies worker time.", type=float, default=9999999)
    parser.add_argument("--num_threads", '-n', help="Number of threads used for scraping.", type=int, default=4)
    args = parser.parse_args()

    start_url = "https://www.dlsu.edu.ph"
    start_node = URLNode(start_url)
    
    lock = threading.Lock()
    url_queue = Queue()
    graph = nx.DiGraph()
    visited = set()
    crawled_urls_data = []
    
    crawl_duration_minutes = args.run_minutes
    scraper_thread_count = args.num_threads 
    
    crawler_thread = threading.Thread(target=bfs, args=(start_node, crawl_duration_minutes, url_queue, lock, graph, visited))
    crawler_thread.start()
    
    scraper_threads = []
    
    for i in range(scraper_thread_count):
        thread = threading.Thread(target=url_processor_worker, args=(url_queue, visited, lock, crawled_urls_data, crawl_duration_minutes))
        thread.start()
        scraper_threads.append(thread)
    
    crawler_thread.join()
    
    for thread in scraper_threads:
        thread.join()
    
    nx.write_graphml(graph, "dlsu_crawl.graphml")
    print("Graph saved as 'dlsu_crawl.graphml'")
    
    write_crawled_urls_to_csv(crawled_urls_data)
    print("Crawled URLs saved to 'crawled_urls.csv'")
   
    write_stats_to_txt(graph, visited)

if __name__ == "__main__":
    main()
