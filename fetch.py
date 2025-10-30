import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from node import Node


def fetch_page(node: Node):
    """Fetch page and extract links within the same domain."""
    try:
        resp = requests.get(node.link, timeout=5)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        a_elements = soup.find_all("a", href=True)

        neighbors = []
        for a in a_elements:
            normalized = Node.normalize(a['href'], base=node.link)
            if "dlsu.edu.ph" not in urlparse(normalized).netloc:
                continue
            neighbors.append(Node(normalized))

        return node.link, neighbors
    except Exception as e:
        print(f"Failed: {node.link} -> {e}")
        return node.link, []