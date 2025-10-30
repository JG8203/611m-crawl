from bs4 import BeautifulSoup, Tag
from typing import Dict
import requests
import time
import threading
from queue import Queue, Empty
import networkx as nx
from node import Node

# Metadata worker
def metadata_worker(url_queue: Queue, visited: set, lock: threading.Lock, results: list, duration: int):
    # Handle duration
    run_time = duration * 60  
    start_time = time.time()
    
    while True:
        
        if time.time() - start_time > run_time:
            print("Time limit reached for metadata worker, stopping.")
            break
        try:
            node: Node = url_queue.get(timeout=5)
        except Empty:
            continue
        
        url = node.link
        with lock:
            if url in visited:
                continue
            visited.add(url)
            
        metadata = extract_metadata(url)
        
        with lock:
            results.append(metadata)
            #DEBUG
            #print(f"Metadata for {url}: Title - {metadata['title']}, Description - {metadata['meta_description']}")


# Get page details
def extract_metadata(url: str) -> Dict[str, str]:
    try:
        resp = requests.get(url, timeout=5)
        resp.raise_for_status()
        soup: BeautifulSoup = BeautifulSoup(resp.text, "html.parser")

        # Extract title safely
        title: str = ""
        if isinstance(soup.title, Tag) and soup.title.string:
            title = soup.title.string.strip()
        else:
            title = "No Title"

        # Extract meta description safely
        meta_description: str = "None"
        meta_tag: Tag | None = soup.find("meta", attrs={"name": "description"})
        if meta_tag and "content" in meta_tag.attrs:
            meta_description = meta_tag["content"].strip()

        return {
            "url": url,
            "title": title,
            "meta_description": meta_description
        }

    except Exception as e:
        #print(f"Failed to get page details for {url} -> {e}")
        return {
            "url": url,
            "title": "Error",
            "meta_description": "None"
        }