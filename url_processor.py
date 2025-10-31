from bs4 import BeautifulSoup, Tag
from typing import Dict
import requests
import time
import threading
from queue import Queue, Empty
import networkx as nx
from node import URLNode

def url_processor_worker(url_queue: Queue, visited: set, lock: threading.Lock, processed_urls_data: list, processing_duration_minutes: int):
    processing_duration_seconds = processing_duration_minutes * 60  
    start_time = time.time()
    
    while True:
        
        if time.time() - start_time > processing_duration_seconds:
            print("Time limit reached for url processor worker, stopping.")
            break
        try:
            url_node: URLNode = url_queue.get(timeout=5)
        except Empty:
            continue
        
        page_url = url_node.url
        with lock:
            if page_url in visited:
                continue
            visited.add(page_url)
            
        extracted_data = extract_url_data(page_url)
        
        with lock:
            processed_urls_data.append(extracted_data)

def extract_url_data(page_url: str) -> Dict[str, str]:
    try:
        response = requests.get(page_url, timeout=5)
        response.raise_for_status()
        beautiful_soup: BeautifulSoup = BeautifulSoup(response.text, "html.parser")

        page_title: str = ""
        if isinstance(beautiful_soup.title, Tag) and beautiful_soup.title.string:
            page_title = beautiful_soup.title.string.strip()
        else:
            page_title = "No Title"

        page_meta_description: str = "None"
        description_meta_tag: Tag | None = beautiful_soup.find("meta", attrs={"name": "description"})
        if description_meta_tag and "content" in description_meta_tag.attrs:
            page_meta_description = description_meta_tag["content"].strip()

        return {
            "url": page_url,
            "title": page_title,
            "meta_description": page_meta_description
        }

    except Exception as e:
        return {
            "url": page_url,
            "title": "Error",
            "meta_description": "None"
        }
