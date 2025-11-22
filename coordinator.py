import threading
import networkx as nx
import Pyro5.api
import Pyro5.server


@Pyro5.api.expose
class Coordinator:
    """
    Pyro5 remote object that manages shared state for distributed crawling.
    Holds the URL queue, visited set, graph, and collected data.
    """

    def __init__(self, seed_url: str):
        self._queue: list[str] = [seed_url]
        self._visited: set[str] = {seed_url}
        self._graph = nx.DiGraph()
        self._graph.add_node(seed_url)
        self._data: list[dict] = []
        self._stop = False
        self._lock = threading.Lock()

    def get_url(self) -> str | None:
        """Get the next URL to crawl. Returns None if queue is empty."""
        with self._lock:
            if self._queue:
                return self._queue.pop(0)
            return None

    def submit_results(self, source_url: str, data: dict, neighbor_urls: list[str]) -> int:
        """
        Submit crawl results: extracted data and discovered neighbor URLs.
        Returns the number of new URLs added to the queue.
        """
        new_count = 0
        with self._lock:
            # Store extracted page data
            if data:
                self._data.append(data)

            # Process neighbor URLs
            for url in neighbor_urls:
                # Add edge to graph
                self._graph.add_edge(source_url, url)

                # Add to queue if not visited
                if url not in self._visited:
                    self._visited.add(url)
                    self._queue.append(url)
                    new_count += 1

        return new_count

    def should_stop(self) -> bool:
        """Check if workers should stop crawling."""
        return self._stop

    def stop(self) -> None:
        """Signal all workers to stop."""
        self._stop = True

    def get_stats(self) -> dict:
        """Get current crawling statistics."""
        with self._lock:
            return {
                "queue_size": len(self._queue),
                "visited_count": len(self._visited),
                "nodes": self._graph.number_of_nodes(),
                "edges": self._graph.number_of_edges(),
                "data_count": len(self._data),
            }

    def get_results(self) -> tuple[list[dict], list[str], int, int]:
        """
        Get final results for output files.
        Returns: (data_list, sorted_urls, node_count, edge_count)
        """
        with self._lock:
            return (
                list(self._data),
                sorted(self._graph.nodes()),
                self._graph.number_of_nodes(),
                self._graph.number_of_edges(),
            )

    def export_graph(self, filename: str) -> None:
        """Export the graph to a GraphML file."""
        with self._lock:
            nx.write_graphml(self._graph, filename)
