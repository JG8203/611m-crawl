import requests
import threading
import time
from queue import Queue, Empty
from bs4 import BeautifulSoup, Tag
from typing import List, Dict, Tuple, Optional
import networkx as nx
from urllib.parse import urlparse

from node import URLNode

def fetch_and_process(url_node: URLNode) -> Optional[Tuple[Dict[str, str], List[URLNode]]]:
    """
    Fetches a single URL and processes it for *both* data and links.
    This combines the work of the old fetch.py and url_processor.py.
    Returns a tuple: (extracted_data, neighbor_nodes) or None on failure.
    """
    try:
        response = requests.get(url_node.url, timeout=5)
        # Raise an exception for bad status codes (4xx, 5xx)
        response.raise_for_status()
        
        # Check content type to avoid parsing non-HTML (e.g., PDFs, images)
        content_type = response.headers.get('Content-Type', '')
        if 'text/html' not in content_type:
            # print(f"Skipping non-HTML: {url_node.url}")
            return None

        soup = BeautifulSoup(response.text, "html.parser")

        # --- 1. Extract Data ---
        page_title = "No Title"
        if isinstance(soup.title, Tag) and soup.title.string:
            page_title = soup.title.string.strip()

        page_meta_description = "None"
        description_tag = soup.find("meta", attrs={"name": "description"})
        if description_tag and "content" in description_tag.attrs:
            page_meta_description = description_tag["content"].strip()
            
        # TODO: Add email extraction logic here as required by the project PDF
        # e.g., using regex to find emails in soup.get_text()

        extracted_data = {
            "url": url_node.url,
            "title": page_title,
            "meta_description": page_meta_description
            # "emails": found_emails_list
        }

        # --- 2. Extract Links (Neighbors) ---
        neighbor_nodes: List[URLNode] = []
        link_elements = soup.find_all("a", href=True)

        for link_element in link_elements:
            normalized_url = URLNode.normalize_url(link_element['href'], base=url_node.url)
            
            # Skip empty or invalid URLs
            if not normalized_url:
                continue

            # Constraint: Only crawl links within the dlsu.edu.ph domain
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
    """
    The main function for each worker thread.
    Continuously pulls URLs, processes them, and adds new URLs back to the queue.
    """
    # Loop until the main thread signals to stop
    while not stop_event.is_set():
        try:
            # Get a URL from the queue.
            # timeout=1 allows the loop to check stop_event regularly
            current_node: URLNode = url_queue.get(timeout=1)
        except Empty:
            # Queue is empty, loop again to check stop_event
            continue
        
        current_url = current_node.url
        
        # --- 1. Fetch and Process (I/O Operation) ---
        # This is the slow part, and it's done *OUTSIDE* all locks.
        # This allows other threads to work in parallel.
        result = fetch_and_process(current_node)

        if result is None:
            # Fetch or processing failed, mark task as done and continue
            url_queue.task_done()
            continue

        extracted_data, neighbor_nodes = result

        # --- 2. Save Extracted Data (Brief Lock) ---
        # This lock is held for a very short time.
        with data_lock:
            processed_urls_data.append(extracted_data)

        # --- 3. Update Topology (Brief Lock) ---
        # This lock protects the graph and visited set.
        with topology_lock:
            for neighbor in neighbor_nodes:
                # Add the edge to the graph
                graph.add_edge(current_url, neighbor.url)
                
                # Check if this neighbor has been seen before
                if neighbor.url not in visited:
                    # If not, add it to visited and put it in the queue
                    visited.add(neighbor.url)
                    url_queue.put(neighbor)
        
        # Signal to the queue that this task is complete
        url_queue.task_done()
