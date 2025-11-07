import requests
import threading
from queue import Queue, Empty
from bs4 import BeautifulSoup, Tag
from typing import List, Dict, Tuple, Optional
import networkx as nx
from urllib.parse import urlparse

from node import URLNode

def fetch_and_process(url_node: URLNode) -> Optional[Tuple[Dict[str, str], List[URLNode]]]:

    try:
        response = requests.get(url_node.url, timeout=5)
        response.raise_for_status()
        
        content_type = response.headers.get('Content-Type', '')
        if 'text/html' not in content_type:
            return None

        soup = BeautifulSoup(response.text, "html.parser")

        # EXTRACT DATA
        page_title = "No Title"
        if isinstance(soup.title, Tag) and soup.title.string:
            page_title = soup.title.string.strip()

        page_meta_description = "None"
        description_tag = soup.find("meta", attrs={"name": "description"})
        if description_tag and "content" in description_tag.attrs:
            page_meta_description = description_tag["content"].strip()
            

        extracted_data = {
            "url": url_node.url,
            "title": page_title,
            "meta_description": page_meta_description
        }

        # EXTRACT LINKS
        neighbor_nodes: List[URLNode] = []
        link_elements = soup.find_all("a", href=True)

        for link_element in link_elements:
            normalized_url = URLNode.normalize_url(link_element['href'], base=url_node.url)
            
            if not normalized_url:
                continue
            
            if "dlsu.edu.ph" not in urlparse(normalized_url).netloc:
                continue
                
            neighbor_nodes.append(URLNode(normalized_url))

        return extracted_data, neighbor_nodes

    except requests.exceptions.RequestException as e:
        # print(f"Failed to fetch {url_node.url}: {e}")
        return None
    except Exception as e:
        # print(f"Failed to process {url_node.url}: {e}")
        return None

def worker(
    url_queue: Queue,
    visited: set,
    graph: nx.DiGraph,
    processed_urls_data: list,
    topology_lock: threading.Lock,
    data_lock: threading.Lock,
    stop_event: threading.Event
):
    
    
    while not stop_event.is_set():
        try:
            current_node: URLNode = url_queue.get(timeout=1)
        except Empty:
            continue
        
        current_url = current_node.url
        
        result = fetch_and_process(current_node)

        if result is None:
            url_queue.task_done()
            continue

        extracted_data, neighbor_nodes = result

        with data_lock:
            processed_urls_data.append(extracted_data)

        with topology_lock:
            for neighbor in neighbor_nodes:
                graph.add_edge(current_url, neighbor.url)
                
                if neighbor.url not in visited:
                    visited.add(neighbor.url)
                    url_queue.put(neighbor)
        
        url_queue.task_done()
