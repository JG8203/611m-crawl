from node import Node
from bfs import bfs
import threading
from queue import Queue
import networkx as nx
from metadata_scraper import metadata_worker
import csv

def write_metadata_to_csv(results, filename="metadata_results.csv"):
    keys = results[0].keys() if results else []
    with open(filename, mode='w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=keys)
        writer.writeheader()
        writer.writerows(results)

def main():
    
    #Define the website to be scraped
    start_url = "https://www.dlsu.edu.ph"
    start_node = Node(start_url)
    
    lock = threading.Lock()
    url_queue = Queue()
    graph = nx.DiGraph()
    visited = set()
    results = []
    
    #TODO: Get user input for duration and max number of threads
    
    #DEBUG: Fixed runtime and threads for testing
    run_minutes = 3  # Change runtime here
    num_threads = 4  # Change number of threads here
    
    #Start BFS crawl
    BFS_thread = threading.Thread(target=bfs, args=(start_node, run_minutes, url_queue, lock, graph, visited))
    BFS_thread.start()
    
    #Create and start threads for metadata scraping
    metadata_threads = []
    
    for _ in range(num_threads):
        #DEBUG
        #print("Starting metadata worker thread")
        t = threading.Thread(target=metadata_worker, args=(url_queue, visited, lock, results, run_minutes))
        t.start()
        metadata_threads.append(t)
    
    BFS_thread.join()
    
    for t in metadata_threads:
        t.join()
    
    # Save graph
    nx.write_graphml(graph, "dlsu_crawl.graphml")
    print("✅ Graph saved as 'dlsu_crawl.graphml'")
    
    #Write metadata results to csv file
    write_metadata_to_csv(results)
    print("✅ Metadata results saved to 'metadata_results.csv'")
    
if __name__ == "__main__":
    main()