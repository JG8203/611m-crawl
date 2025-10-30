from node import Node
from bfs import bfs
import threading
from queue import Queue
import networkx as nx

if __name__ == "__main__":
    
    #Define the website to be scraped
    start_url = "https://www.dlsu.edu.ph"
    start_node = Node(start_url)
    
    lock = threading.Lock()
    url_queue = Queue()
    graph = nx.DiGraph()
    visited = set()
    
    #TODO: Get user input for duration and max number of threads
    
    #DEBUG: Fixed runtime and threads for testing
    run_minutes = 1  # Change runtime here
    num_threads = 4  # Change number of threads here
    
    #Start BFS crawl
    BFS_thread = threading.Thread(target=bfs, args=(start_node, run_minutes, url_queue, lock, graph, visited))
    BFS_thread.start()
    
    #Create and start threads for email scraping
    
    BFS_thread.join()
    
    # Save graph
    nx.write_graphml(graph, "dlsu_crawl.graphml")
    print("✅ Graph saved as 'dlsu_crawl.graphml'")
    
