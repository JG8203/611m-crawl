import re
import requests
from bs4 import BeautifulSoup, SoupStrainer
from urllib.parse import urlparse, unquote
import Pyro5.api

from node import URLNode


def extract_pdf_filename(url: str) -> str:
    """Extract filename from PDF URL path."""
    path = urlparse(url).path
    filename = path.split("/")[-1]
    # URL decode and remove .pdf extension for cleaner title
    filename = unquote(filename)
    if filename.lower().endswith(".pdf"):
        filename = filename[:-4]
    return filename or "PDF Document"


def fetch_and_process(url: str) -> tuple[dict, list[str]] | None:
    """
    Fetch a page and extract data and links.
    Returns (extracted_data, neighbor_urls) or None on failure.
    """
    try:
        # Handle PDF URLs - extract filename as title, no links
        if urlparse(url).path.lower().endswith(".pdf"):
            extracted_data = {
                "url": url,
                "title": extract_pdf_filename(url),
                "meta_description": "PDF Document",
            }
            return extracted_data, []

        # Stream HTML response
        response = requests.get(url, timeout=5, stream=True)
        response.raise_for_status()

        content_type = response.headers.get("Content-Type", "")
        if "text/html" not in content_type:
            return None

        # Read content in chunks, stop early once we have </head>
        content = ""
        title_found = False
        page_title = "No Title"
        page_meta_description = "None"

        for chunk in response.iter_content(chunk_size=4096, decode_unicode=True):
            if chunk:
                content += chunk

            # Try to extract title early
            if not title_found and "</title>" in content.lower():
                match = re.search(r"<title[^>]*>(.*?)</title>", content, re.IGNORECASE | re.DOTALL)
                if match:
                    page_title = match.group(1).strip()
                    title_found = True

            # Extract meta description from head (handle both attribute orders)
            if "</head>" in content.lower() and page_meta_description == "None":
                # Try name before content
                match = re.search(
                    r'<meta[^>]*name=["\']description["\'][^>]*content=["\'](.*?)["\']',
                    content,
                    re.IGNORECASE,
                )
                if not match:
                    # Try content before name
                    match = re.search(
                        r'<meta[^>]*content=["\'](.*?)["\'][^>]*name=["\']description["\']',
                        content,
                        re.IGNORECASE,
                    )
                if match:
                    page_meta_description = match.group(1).strip()

        extracted_data = {
            "url": url,
            "title": page_title,
            "meta_description": page_meta_description,
        }

        # Parse only <a> tags for links using SoupStrainer
        link_strainer = SoupStrainer("a", href=True)
        soup = BeautifulSoup(content, "html.parser", parse_only=link_strainer)

        neighbor_urls: list[str] = []
        for link_element in soup:
            normalized_url = URLNode.normalize_url(link_element["href"], base=url)

            if not normalized_url:
                continue

            if "dlsu.edu.ph" not in urlparse(normalized_url).netloc:
                continue

            neighbor_urls.append(normalized_url)

        return extracted_data, neighbor_urls

    except requests.exceptions.RequestException:
        return None
    except Exception:
        return None


def run_worker(coordinator_uri: str) -> None:
    """
    Connect to coordinator and process URLs until stopped.
    """
    coordinator = Pyro5.api.Proxy(coordinator_uri)

    while True:
        # Check if we should stop
        if coordinator.should_stop():
            break

        # Get next URL from coordinator
        url = coordinator.get_url()
        print(f"Received {url} from coordinator :D")

        if url is None:
            # Queue is empty, wait a bit and try again
            import time
            time.sleep(0.5)
            continue

        # Fetch and process the page
        result = fetch_and_process(url)

        if result is None:
            # Failed to fetch, continue with next URL
            continue

        extracted_data, neighbor_urls = result

        # Submit results to coordinator
        coordinator.submit_results(url, extracted_data, neighbor_urls)
