from __future__ import annotations
from typing import Optional, List, Set, Deque
from collections import deque
from urllib.parse import urljoin, urldefrag, urlparse, urlunparse
from DrissionPage import ChromiumPage
import networkx as nx
import re

class Node:
    def __init__(
        self,
        link: str,
        page: Optional[ChromiumPage] = None,
        neighbors: Optional[List["Node"]] = None,
        base: Optional[str] = None,
    ) -> None:
        self.link: str = self.normalize(link, base)
        self.page: Optional[ChromiumPage] = page
        self.neighbors: List[Node] = neighbors or []

    @staticmethod
    def normalize(link: str, base: Optional[str] = None) -> str:
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

    def __hash__(self) -> int:
        return hash(self.link)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Node) and self.link == other.link

    def __repr__(self) -> str:
        return f"Node({self.link!r})"


def bfs(start: Node, max_pages: int = 5000) -> List[str]:
    visited: Set[str] = set()
    queue: Deque[Node] = deque([start])
    pages_crawled = 0
    visited_links: List[str] = []

    # Create a directed graph
    G = nx.DiGraph()

    browser = ChromiumPage()

    while queue and pages_crawled < max_pages:
        node: Node = queue.popleft()

        if node.link in visited:
            continue

        visited.add(node.link)
        visited_links.append(node.link)
        pages_crawled += 1

        print(f"Crawling ({pages_crawled}/{max_pages}): {node.link}")

        try:
            browser.get(node.link, timeout=3)
            a_elements: List[object] = browser.eles("tag:a")
            
            #✅ Extract emails from the page
            emails = extract_emails(browser, node.link)
            print(f"  Emails found: {', '.join(emails) if emails else 'None'}")
            
        except Exception as e:
            print(f"Failed to extract links from {node.link}: {e}")
            continue
        

        neighbors: List[Node] = []
        for a in a_elements:
            href = a.attr("href")
            if not href:
                continue

            normalized = Node.normalize(href, base=node.link)
            parsed = urlparse(normalized)

            # ✅ Only add links within dlsu.edu.ph domain
            if "dlsu.edu.ph" not in parsed.netloc:
                continue

            if normalized and normalized not in visited:
                neighbor = Node(normalized)
                neighbors.append(neighbor)
                queue.append(neighbor)

            # ✅ Add edge to graph
            G.add_edge(node.link, normalized)

        node.neighbors = neighbors

    browser.quit()

    # ✅ Save graph to GraphML
    nx.write_graphml(G, "dlsu_crawl.graphml")
    print("\n✅ Graph saved as 'dlsu_crawl.graphml'")

    return visited_links

def extract_emails(page: ChromiumPage, current_url: str) -> List[str]:
    """Extract email addresses from the given text."""
    
    try:
        html = page.html
    except Exception as e:
        print(f"Failed to get page source from {current_url}: {e}")
        return []
    
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    emails = re.findall(email_pattern, html)
    emails=list(set(emails))
    
    if emails:
        print(f"  Found emails on {current_url}: {', '.join(emails)}")
        
    return emails

def main(url: str) -> List[str]:
    root = Node(url)
    visited_links = bfs(root)
    print(f"\nCrawled {len(visited_links)} pages")
    return visited_links


if __name__ == "__main__":
    
    #--------------------------
    # Ask user for input
    #--------------------------
    #url = input("Enter the starting URL (default: http://www.dlsu.edu.ph): ")
    #duration = input("Enter duration in minutes (default: 60): ")
    #num_threads = input("Enter number of threads (default: 4): ")
    
    #print(f"Starting crawl with URL: {url or 'http://www.dlsu.edu.ph'}, Duration: {duration or '60'} minutes, Threads: {num_threads or '4'}\n")
    
    
    
    
    links = main("http://www.dlsu.edu.ph")
    print("\nVisited links:")
    for link in links:
        print(f"  - {link}")

