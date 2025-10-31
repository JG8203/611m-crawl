import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from node import URLNode
from typing import List


def fetch_page_and_extract_links(url_node: URLNode):
    try:
        response = requests.get(url_node.url, timeout=5)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        link_elements = soup.find_all("a", href=True)

        neighbor_nodes: List[URLNode] = []
        for link_element in link_elements:
            normalized_url = URLNode.normalize_url(link_element['href'], base=url_node.url)
            if "dlsu.edu.ph" not in urlparse(normalized_url).netloc:
                continue
            neighbor_nodes.append(URLNode(normalized_url))

        return url_node.url, neighbor_nodes
    except Exception as e:
        print(f"Failed: {url_node.url} -> {e}")
        return url_node.url, []
