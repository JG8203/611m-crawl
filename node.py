from urllib.parse import urljoin, urldefrag, urlparse, urlunparse

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