from collections import deque
import time
import networkx as nx
from node import Node
from fetch import fetch_page
from queue import Queue, Empty
import threading

def bfs(start: Node, duration: int, queue : Queue, lock: threading.Lock, graph: nx.DiGraph, visited: set):
    #visited = set()
    #queue = deque([start])
    G = nx.DiGraph()
    visited_links = []
    pages_crawled = 0
    
    # Handle duration
    run_time = duration * 60  
    start_time = time.time()
    
    queue.put(start)

    while True:
        
        if time.time() - start_time > run_time:
            print("Time limit reached, stopping crawl.")
            break
        
        try:
            node: Node = queue.get()
        except Empty:
            print("Queue is empty, stopping crawl.")
            break
        
        with lock:    
            if node.link in visited:
                continue
            visited.add(node.link)

        visited_links.append(node.link)
        pages_crawled += 1
        
        #DEBUG Print statement
        print(f"Crawled ({pages_crawled}): {node.link}")

        # Fetch page and get neighbors
        link, neighbors = fetch_page(node)

        # Add neighbors to queue if not visited
        for neighbor in neighbors:
            with lock:
                if neighbor.link not in visited:
                    queue.put(neighbor)
                G.add_edge(link, neighbor.link)

    return visited_links, G
