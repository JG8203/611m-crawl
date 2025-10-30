from node import Node
from bfs import bfs

if __name__ == "__main__":
    start_url = "https://www.dlsu.edu.ph"
    start_node = Node(start_url)
    run_minutes = 1  # Change runtime here

    visited_links, G = bfs(start_node, run_minutes)

    print(f"\nVisited {len(visited_links)} pages.")
