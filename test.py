import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urldefrag, urlparse, urlunparse
from collections import deque
import time
import networkx as nx

class Node:
    def __init__(self, link: str, neighbors=None, base: str = None):
        self.link = self.normalize(link, base)
        self.neighbors = neighbors or []

    @staticmethod
    def normalize(link: str, base: str = None) -> str:
        if not link:
            return ""
        if base:
            link = urljoin(base, link)
        link, _ = urldefrag(link)
        parsed = urlparse(link)
        scheme = (parsed.scheme or "http").lower()
        netloc = parsed.netloc.lower()
        path = parsed.path or "/"
        return urlunparse((scheme, netloc, path, parsed.params, parsed.query, ""))

    def __hash__(self):
        return hash(self.link)

    def __eq__(self, other):
        return isinstance(other, Node) and self.link == other.link

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

#Time duration in minutes
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

if __name__ == "__main__":
    start_url = "https://www.dlsu.edu.ph"
    start_node = Node(start_url)
    visited = bfs(start_node, duration=1)  # Duration in minutes

    print("\nVisited links:", visited)

    
# --- Email Extraction Utilities ---

import re
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import requests

EMAIL_REGEX = re.compile(
    r'(?:mailto:)?[\'"‘“]?\b([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,})\b[\'"’”]?',
    re.IGNORECASE
)

# Decrypt Cloudflare protected email
def cfDecodeEmail(encodedString):
    try:    
        r = int(encodedString[:2],16)
        email = ''.join([chr(int(encodedString[i:i+2], 16) ^ r) for i in range(2, len(encodedString), 2)])
    except Exception as e:
        print(f"Error decoding Cloudflare email: {e}")
        email = None
    return email

#Find emails
def find_emails(html: str, url: str):
    results = []        #TODO: Handle emails with affiliations and names
    emails = []
    
    # TODO: Handle affiliations and names
    soup = BeautifulSoup(html, "html.parser")
    
    text_content = soup.get_text(separator=" ", strip=True)
    for match in EMAIL_REGEX.findall(text_content):
        emails.append(match)

            
    #Find Cloudflare protected emails
    for span in soup.find_all('span', class_="__cf_email__"):
        
        #DEBUG
        #print(span)
        
        data_cfemail = span.get('data-cfemail')
        if data_cfemail:
            email = cfDecodeEmail(data_cfemail)
            if EMAIL_REGEX.match(email):
                emails.append(email)
                
    return emails   #TODO: Return affiliations and names as well
