from collections import deque
import time
import networkx as nx
from node import Node
from fetch import fetch_page

def bfs(start: Node, duration: int):
    visited = set()
    queue = deque([start])
    visited_links = []
    G = nx.DiGraph()
    pages_crawled = 0
    
    # Convert to minutes to seconds
    duration = duration * 60  
    start_time = time.time()

    while queue:
        
        if time.time() - start_time > duration:
            print("Time limit reached, stopping crawl.")
            break
        
        node = queue.popleft()

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
            if neighbor.link not in visited:
                queue.append(neighbor)
            G.add_edge(link, neighbor.link)

    # Save graph
    nx.write_graphml(G, "dlsu_crawl.graphml")
    print("✅ Graph saved as 'dlsu_crawl.graphml'")

    return visited_links, G
