from urllib.parse import urljoin, urldefrag, urlparse, urlunparse

class URLNode:
    """A simple class to represent a URL and handle normalization."""
    
    def __init__(self, url: str, base: str = None):
        self.url = self.normalize_url(url, base)

    @staticmethod
    def normalize_url(url: str, base: str = None) -> str:
        """
        Normalizes a URL by joining with base, removing fragments,
        and standardizing scheme/netloc.
        """
        if not url:
            return ""
            
        # Join relative URLs with their base
        if base:
            url = urljoin(base, url)
            
        # Remove the fragment (e.g., #section1)
        url, _ = urldefrag(url)
        
        parsed = urlparse(url)
        
        # Default to http if no scheme is present
        scheme = (parsed.scheme or "http").lower()
        
        # Lowercase the domain
        netloc = parsed.netloc.lower()
        
        # Set a default path if empty
        path = parsed.path or "/"
        
        # Reconstruct the URL
        return urlunparse((scheme, netloc, path, parsed.params, parsed.query, ""))

    def __hash__(self):
        return hash(self.url)

    def __eq__(self, other):
        return isinstance(other, URLNode) and self.url == other.url

    def __repr__(self) -> str:
        return f"URLNode({self.url!r})"
