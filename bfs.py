from collections import deque
import time
import networkx as nx
from node import URLNode
from fetch import fetch_page_and_extract_links
from queue import Queue, Empty
import threading

def bfs(start_node: URLNode, crawl_duration_minutes: int, url_queue : Queue, lock: threading.Lock, graph: nx.DiGraph, visited: set):
    visited_links = []
    pages_crawled = 0
    
    crawl_duration_seconds = crawl_duration_minutes * 60  
    start_time = time.time()
    
    url_queue.put(start_node)

    while True:
        
        if time.time() - start_time > crawl_duration_seconds:
            print("Time limit reached, stopping crawl.")
            break
        
        try:
            current_node: URLNode = url_queue.get()
        except Empty:
            print("Queue is empty, stopping crawl.")
            break
        
        with lock:    
            if current_node.url in visited:
                continue
            visited.add(current_node.url)

        visited_links.append(current_node.url)
        pages_crawled += 1
        
        print(f"Crawled ({pages_crawled}): {current_node.url}")

        current_url, neighbor_nodes = fetch_page_and_extract_links(current_node)
        for neighbor_node in neighbor_nodes:
            with lock:
                if neighbor_node.url not in visited:
                    url_queue.put(neighbor_node)
                graph.add_edge(current_url, neighbor_node.url)

    return visited_links, graph
