from node import Node
from bfs import bfs
import threading
from queue import Queue
import networkx as nx
from metadata_scraper import metadata_worker

if __name__ == "__main__":
    
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
    run_minutes = 1  # Change runtime here
    num_threads = 4  # Change number of threads here
    
    #Start BFS crawl
    BFS_thread = threading.Thread(target=bfs, args=(start_node, run_minutes, url_queue, lock, graph, visited))
    BFS_thread.start()
    
    #Create and start threads for metadata scraping
    metadata_threads = []
    for _ in range(num_threads):
        t = threading.Thread(target=metadata_worker, args=(url_queue, visited, lock, results, run_minutes))
        t.start()
        metadata_threads.append(t)
    
    BFS_thread.join()
    
    for t in metadata_threads:
        t.join()
    
    
    # metadata_results = []
    # while not url_queue.empty():
    #     node: Node = url_queue.get()
    #     current_url = node.link
        
    #     #print(f"Extracting metadata from: {current_url}")
    #     metadata = extract_metadata(current_url)
    #     metadata_results.append(metadata)
    #     print(f"Metadata for {current_url}: Title - {metadata['title']}, Description - {metadata['meta_description']}")
    
    # Save graph
    nx.write_graphml(graph, "dlsu_crawl.graphml")
    print("✅ Graph saved as 'dlsu_crawl.graphml'")
    
