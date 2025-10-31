from urllib.parse import urljoin, urldefrag, urlparse, urlunparse

class URLNode:
    def __init__(self, url: str, neighbor_nodes=None, base: str = None):
        self.url = self.normalize_url(url, base)
        self.neighbor_nodes = neighbor_nodes or []

    @staticmethod
    def normalize_url(url: str, base: str = None) -> str:
        if not url:
            return ""
        if base:
            url = urljoin(base, url)
        url, _ = urldefrag(url)
        parsed = urlparse(url)
        scheme = (parsed.scheme or "http").lower()
        netloc = parsed.netloc.lower()
        path = parsed.path or "/"
        return urlunparse((scheme, netloc, path, parsed.params, parsed.query, ""))

    def __hash__(self):
        return hash(self.url)

    def __eq__(self, other):
        return isinstance(other, URLNode) and self.url == other.url

    def __repr__(self) -> str:
        return f"URLNode({self.url!r})"
