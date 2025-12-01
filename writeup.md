# Distributed Web Crawler Implementation Using Pyro5

**CSC611M - Distributed Programming Project**
**De La Salle University - Computer Technology Department**

---

## Abstract

This paper presents the design, implementation, and performance analysis of a distributed web crawler system built using Pyro5 (Python Remote Objects). The system employs a coordinator-worker architecture to parallelize the crawling of the De La Salle University website (`https://www.dlsu.edu.ph`). Our implementation demonstrates significant performance improvements when scaling from 1 to 16 worker nodes, achieving up to 3.5x increase in pages discovered within a fixed time period. The system utilizes remote procedure calls (RPC) for inter-process communication, centralized coordination for URL queue management, and containerization via Docker for deployment across distributed nodes.

---

## 1. Introduction

### 1.1 Background

Web crawlers are automated programs that systematically browse the internet to index web pages and extract information. Modern search engines and large language models (LLMs) rely heavily on web crawlers to discover and process web content. Given the vast scale of the internet, efficient web crawling requires parallel and distributed computing techniques to achieve reasonable performance.

### 1.2 Project Objectives

The primary objectives of this project are:

1. **Develop a distributed web crawler** capable of extracting URLs and metadata from `https://www.dlsu.edu.ph`
2. **Implement distributed system techniques** including coordination, synchronization, and message passing
3. **Deploy across multiple nodes** using containerization technology
4. **Analyze performance scaling** with varying numbers of worker nodes

### 1.3 Requirements Summary

| Requirement | Implementation |
|-------------|----------------|
| Target Website | `https://www.dlsu.edu.ph` |
| Input Parameters | URL, duration (minutes), number of nodes |
| Output Files | CSV (URLs + descriptions), TXT (statistics), GraphML (link topology) |
| Distributed Nodes | Docker containers (scalable 1-16+ workers) |
| Middleware | Pyro5 (Python Remote Objects) |

---

## 2. System Architecture

### 2.1 High-Level Architecture

The system follows a **coordinator-worker** (master-slave) architecture pattern, which is well-suited for distributed crawling tasks:

```
┌─────────────────────────────────────────────────────────────────┐
│                        COORDINATOR NODE                          │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                   Coordinator Server                      │    │
│  │  ┌───────────┐  ┌───────────┐  ┌───────────────────┐    │    │
│  │  │ URL Queue │  │  Visited  │  │   NetworkX Graph  │    │    │
│  │  │  (FIFO)   │  │    Set    │  │   (Link Topology) │    │    │
│  │  └───────────┘  └───────────┘  └───────────────────┘    │    │
│  │  ┌───────────────────┐  ┌─────────────────────────┐     │    │
│  │  │   Extracted Data  │  │   Threading Lock        │     │    │
│  │  │   (URL + Title)   │  │   (Synchronization)     │     │    │
│  │  └───────────────────┘  └─────────────────────────┘     │    │
│  └─────────────────────────────────────────────────────────┘    │
│                              │                                   │
│                        Pyro5 Daemon                              │
│                         (Port 9999)                              │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                    Pyro5 RPC (TCP/IP)
                               │
        ┌──────────────────────┼──────────────────────┐
        │                      │                      │
        ▼                      ▼                      ▼
┌───────────────┐    ┌───────────────┐      ┌───────────────┐
│   Worker 1    │    │   Worker 2    │ ...  │   Worker N    │
│               │    │               │      │               │
│ ┌───────────┐ │    │ ┌───────────┐ │      │ ┌───────────┐ │
│ │  Fetcher  │ │    │ │  Fetcher  │ │      │ │  Fetcher  │ │
│ │  (HTTP)   │ │    │ │  (HTTP)   │ │      │ │  (HTTP)   │ │
│ └───────────┘ │    │ └───────────┘ │      │ └───────────┘ │
│ ┌───────────┐ │    │ ┌───────────┐ │      │ ┌───────────┐ │
│ │  Parser   │ │    │ │  Parser   │ │      │ │  Parser   │ │
│ │   (BS4)   │ │    │ │   (BS4)   │ │      │ │   (BS4)   │ │
│ └───────────┘ │    │ └───────────┘ │      │ └───────────┘ │
└───────────────┘    └───────────────┘      └───────────────┘
```

### 2.2 Component Overview

| Component | File | Responsibility |
|-----------|------|----------------|
| **Coordinator** | `coordinator.py` | Centralized state management, URL distribution, result aggregation |
| **Worker Client** | `client.py` | HTTP fetching, HTML parsing, link extraction |
| **URL Normalizer** | `node.py` | URL canonicalization and deduplication |
| **Server Entry** | `run_server.py` | Coordinator initialization and output generation |
| **Client Entry** | `run_client.py` | Worker connection and lifecycle management |

### 2.3 Communication Protocol

The system uses **Pyro5** (Python Remote Objects version 5) for inter-process communication. Pyro5 provides:

- **Remote Procedure Calls (RPC)**: Workers invoke methods on the coordinator as if they were local
- **Automatic Serialization**: Python objects are transparently serialized/deserialized using the Serpent serializer
- **Connection Management**: Handles TCP connections, reconnection, and timeouts
- **Thread Safety**: Multiple concurrent RPC calls are handled safely

**Pyro5 URI Format:**
```
PYRO:crawler.coordinator@<host>:<port>
Example: PYRO:crawler.coordinator@coordinator:9999
```

---

## 3. Implementation Details

### 3.1 Coordinator Server (`coordinator.py`)

The coordinator is implemented as a Pyro5-exposed class that manages all shared state:

```python
@Pyro5.api.expose
class Coordinator:
    def __init__(self, seed_url: str):
        self._queue: list[str] = [seed_url]     
        self._visited: set[str] = {seed_url}   
        self._graph = nx.DiGraph()            
        self._data: list[dict] = []             
        self._stop = False                
        self._lock = threading.Lock()            
```

**Key Methods:**

| Method | Description |
|--------|-------------|
| `get_url()` | Dequeues next URL for a worker (returns `None` if empty) |
| `submit_results(url, data, neighbors)` | Receives crawl results, updates graph, enqueues new URLs |
| `should_stop()` | Workers poll this to check for termination signal |
| `get_stats()` | Returns current queue size, visited count, etc. |

**Thread Safety:**

All state-modifying operations are protected by a `threading.Lock()` to ensure consistency when multiple workers make concurrent RPC calls:

```python
def submit_results(self, source_url: str, data: dict, neighbor_urls: list[str]) -> int:
    with self._lock:
        if data:
            self._data.append(data)
        for url in neighbor_urls:
            self._graph.add_edge(source_url, url)
            if url not in self._visited:
                self._visited.add(url)
                self._queue.append(url)
```

### 3.2 Worker Client (`client.py`)

Workers operate in a stateless loop, fetching URLs from the coordinator and submitting results:

```python
def run_worker(coordinator_uri: str) -> None:
    coordinator = Pyro5.api.Proxy(coordinator_uri)

    while True:
        if coordinator.should_stop():
            break

        url = coordinator.get_url()
        if url is None:
            time.sleep(0.5)  # Backoff when queue empty
            continue

        result = fetch_and_process(url)
        if result:
            extracted_data, neighbor_urls = result
            coordinator.submit_results(url, extracted_data, neighbor_urls)
```

**HTML Fetching Optimizations:**

1. **Streaming Response**: Uses `requests.get(url, stream=True)` to read chunks incrementally
2. **Early Title Extraction**: Extracts `<title>` as soon as `</title>` is encountered using regex
3. **Selective Parsing**: Uses `BeautifulSoup` with `SoupStrainer` to parse only `<a>` tags
4. **PDF Handling**: Extracts filename from URL path for PDF files without downloading

```python
# Streaming with early extraction
for chunk in response.iter_content(chunk_size=4096, decode_unicode=True):
    content += chunk
    if not title_found and "</title>" in content.lower():
        match = re.search(r"<title[^>]*>(.*?)</title>", content, re.IGNORECASE | re.DOTALL)
        if match:
            page_title = match.group(1).strip()
            title_found = True

# Efficient link parsing
link_strainer = SoupStrainer("a", href=True)
soup = BeautifulSoup(content, "html.parser", parse_only=link_strainer)
```

### 3.3 URL Normalization (`node.py`)

Proper URL normalization is critical to avoid crawling duplicate pages:

```python
@staticmethod
def normalize_url(url: str, base: str = None) -> str:
    if base:
        url = urljoin(base, url)           # Resolve relative URLs
    url, _ = urldefrag(url)                 # Remove fragments (#...)
    parsed = urlparse(url)
    scheme = (parsed.scheme or "http").lower()
    netloc = parsed.netloc.lower()          # Lowercase domain
    path = parsed.path or "/"
    return urlunparse((scheme, netloc, path, parsed.params, parsed.query, ""))
```

**Normalization Rules:**
- Join relative URLs with base URL
- Remove URL fragments (e.g., `#section`)
- Lowercase scheme and domain
- Default empty path to `/`

### 3.4 Domain Filtering

Only URLs within the `dlsu.edu.ph` domain are followed:

```python
if "dlsu.edu.ph" not in urlparse(normalized_url).netloc:
    continue
```

This includes subdomains like `www.dlsu.edu.ph`, `animospace.dlsu.edu.ph`, etc.

### 3.5 Containerization (`Dockerfile`, `docker-compose.yml`)

**Dockerfile:**
```dockerfile
FROM python:3.13-slim
WORKDIR /app
RUN pip install --no-cache-dir pyro5 requests networkx beautifulsoup4
COPY node.py coordinator.py client.py run_server.py run_client.py ./
CMD ["python", "run_server.py"]
```

**Docker Compose Configuration:**
```yaml
services:
  coordinator:
    build: .
    container_name: crawler-coordinator-bs
    command: python run_server.py -u http://www.dlsu.edu.ph -t ${CRAWL_MINUTES:-2} -H 0.0.0.0 -p 9999 -o /output
    ports:
      - "9999:9999"
    volumes:
      - ./output:/output

  worker:
    build: .
    command: ["python", "-u", "run_client.py", "-H", "coordinator", "-p", "9999", "-d", "3"]
    depends_on:
      - coordinator
    restart: on-failure
```

**Scaling Workers:**
```bash
docker compose up --scale worker=16
```

---

## 4. Distributed Systems Techniques

### 4.1 Coordination

The coordinator acts as a **central point of coordination**, managing:

1. **Work Distribution**: URL queue ensures each URL is processed exactly once
2. **State Synchronization**: Visited set prevents duplicate crawling
3. **Result Aggregation**: All extracted data flows back to the coordinator

### 4.2 Message Passing

Pyro5 provides **transparent RPC-based message passing**:

| Operation | Direction | Message Content |
|-----------|-----------|-----------------|
| `get_url()` | Worker → Coordinator → Worker | Request: none, Response: URL string |
| `submit_results()` | Worker → Coordinator | URL, extracted data dict, neighbor URLs list |
| `should_stop()` | Worker → Coordinator → Worker | Request: none, Response: boolean |

### 4.3 Synchronization

**Threading Lock** ensures mutual exclusion when multiple workers concurrently access shared state:

```python
with self._lock:
    # Critical section - only one thread at a time
    self._data.append(data)
    for url in neighbor_urls:
        if url not in self._visited:
            self._visited.add(url)
            self._queue.append(url)
```

### 4.4 Fault Tolerance

- **Connection Retry**: Workers retry connection up to 10 times with 2-second delays
- **Container Restart**: Docker's `restart: on-failure` policy restarts crashed workers
- **Graceful Shutdown**: Coordinator signals workers via `should_stop()` flag

---

## 5. Results and Analysis

### 5.1 Experimental Setup

| Parameter | Value |
|-----------|-------|
| Target Website | `https://www.dlsu.edu.ph` |
| Crawl Duration | 2 minutes per test |
| Worker Configurations | 1, 2, 4, 8, 16 workers |
| Trials per Configuration | 3 |
| Total Tests | 15 |
| Environment | Docker containers on single host |

### 5.2 Performance Results

#### Trial 1

| Workers | Pages Discovered | Links Found | Pages/Worker |
|---------|------------------|-------------|--------------|
| 1 | 2,075 | 15,347 | 2,075 |
| 2 | 3,291 | 37,250 | 1,646 |
| 4 | 4,153 | 61,607 | 1,038 |
| 8 | 5,715 | 90,474 | 714 |
| 16 | 7,129 | 129,963 | 446 |

#### Trial 2

| Workers | Pages Discovered | Links Found | Pages/Worker |
|---------|------------------|-------------|--------------|
| 1 | 2,160 | 15,946 | 2,160 |
| 2 | 2,954 | 29,265 | 1,477 |
| 4 | 3,955 | 53,501 | 989 |
| 8 | 5,604 | 93,878 | 701 |
| 16 | 7,222 | 129,005 | 451 |

#### Trial 3

| Workers | Pages Discovered | Links Found | Pages/Worker |
|---------|------------------|-------------|--------------|
| 1 | 2,480 | 18,146 | 2,480 |
| 2 | 3,091 | 34,309 | 1,546 |
| 4 | 3,639 | 44,819 | 910 |
| 8 | 5,772 | 92,754 | 722 |
| 16 | 7,660 | 148,707 | 479 |

### 5.3 Average Performance Summary

| Workers | Avg Pages | Avg Links | Speedup vs 1 Worker |
|---------|-----------|-----------|---------------------|
| 1 | 2,238 | 16,480 | 1.00x |
| 2 | 3,112 | 33,608 | 1.39x |
| 4 | 3,916 | 53,309 | 1.75x |
| 8 | 5,697 | 92,369 | 2.55x |
| 16 | 7,337 | 135,892 | 3.28x |

### 5.4 Performance Analysis

#### Scaling Efficiency

```
Speedup Chart (Pages Discovered):

16 workers: ████████████████████████████████░░░░░░░░ 3.28x
 8 workers: ████████████████████░░░░░░░░░░░░░░░░░░░░ 2.55x
 4 workers: ██████████████░░░░░░░░░░░░░░░░░░░░░░░░░░ 1.75x
 2 workers: ██████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ 1.39x
 1 worker:  ████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ 1.00x
```

#### Observations

1. **Sub-linear Scaling**: Doubling workers does not double throughput
   - 2x workers → ~1.4x pages
   - 4x workers → ~1.75x pages
   - 8x workers → ~2.55x pages
   - 16x workers → ~3.28x pages

2. **Bottleneck Analysis**:
   - **Network I/O**: All containers share the same network interface
   - **Coordinator Contention**: Single coordinator handles all RPC calls
   - **Website Rate Limiting**: Target server may throttle requests
   - **Queue Starvation**: Workers may idle waiting for new URLs early in crawl

3. **Diminishing Returns**: Per-worker efficiency decreases with more workers
   - 1 worker: 2,238 pages/worker
   - 16 workers: 459 pages/worker (20% efficiency)

4. **Consistency**: Results are relatively consistent across trials (±10% variance)

### 5.5 Output Files

**Sample CSV Output (`crawled_urls.csv`):**
```csv
url,title,meta_description
http://www.dlsu.edu.ph/,De La Salle University,"De La Salle University (DLSU) is a leading university..."
https://www.dlsu.edu.ph/about-dlsu/,About - De La Salle University,"Nestled in the heart of Manila..."
http://www.dlsu.edu.ph/inside/,Quick Facts and Figures - De La Salle University,None
```

**Sample Metadata Output (`metadata.txt`):**
```
Total pages discovered: 7129
Total pages visited: 7129
Total links found: 129963

Visited URLs:
- http://www.dlsu.edu.ph/
- http://www.dlsu.edu.ph/about-dlsu
- http://www.dlsu.edu.ph/academics
...
```

---

## 6. Conclusion

### 6.1 Summary

This project successfully implemented a distributed web crawler using the Pyro5 middleware for remote procedure calls. The coordinator-worker architecture effectively distributes crawling workload across multiple containerized nodes while maintaining data consistency through centralized coordination.

### 6.2 Key Achievements

1. **Distributed Architecture**: Successfully deployed across multiple Docker containers with Pyro5-based communication
2. **Scalability**: Demonstrated performance improvements up to 3.28x with 16 workers
3. **Data Consistency**: Centralized visited set ensures each URL is crawled exactly once
4. **Fault Tolerance**: Workers can reconnect after failures; containers auto-restart

### 6.3 Distributed Systems Techniques Applied

| Technique | Implementation |
|-----------|----------------|
| **Remote Procedure Call** | Pyro5 for transparent method invocation |
| **Coordination** | Central coordinator manages URL queue and visited set |
| **Synchronization** | Threading locks protect shared state |
| **Message Passing** | Pyro5 serializes and transmits Python objects |
| **Containerization** | Docker enables deployment across nodes |

### 6.4 Limitations and Future Work

1. **Single Point of Failure**: Coordinator failure stops entire system
   - *Future*: Implement coordinator replication or distributed hash table

2. **Scalability Ceiling**: Coordinator becomes bottleneck at high worker counts
   - *Future*: Partition URL space across multiple coordinators

3. **Same-Host Testing**: All containers ran on single machine
   - *Future*: Deploy across multiple physical/cloud machines

4. **No Politeness**: No respect for `robots.txt` or crawl delays
   - *Future*: Implement politeness policies

---

## 7. References

1. **Pyro5 Documentation**
   Irmen de Jong. "Pyro5 - Python Remote Objects."
   https://github.com/irmen/Pyro5

2. **BeautifulSoup Documentation**
   Leonard Richardson. "Beautiful Soup Documentation."
   https://www.crummy.com/software/BeautifulSoup/bs4/doc/

3. **NetworkX Documentation**
   Aric Hagberg, Dan Schult, Pieter Swart. "NetworkX: Network Analysis in Python."
   https://networkx.org/documentation/stable/

4. **Docker Documentation**
   Docker Inc. "Docker Compose Overview."
   https://docs.docker.com/compose/

5. **Web Crawling Concepts**
   Christopher Olston, Marc Najork. "Web Crawling."
   Foundations and Trends in Information Retrieval, 2010.

6. **Distributed Systems Principles**
   Andrew S. Tanenbaum, Maarten Van Steen. "Distributed Systems: Principles and Paradigms."
   Pearson Education, 2007.

---

## Appendix A: File Structure

```
Code_2/
├── coordinator.py      # Pyro5 coordinator server class
├── client.py           # Worker client with fetch logic
├── node.py             # URL normalization utility
├── run_server.py       # Coordinator entry point
├── run_client.py       # Worker entry point
├── Dockerfile          # Container image definition
├── docker-compose.yml  # Multi-container orchestration
├── run_tests.sh        # Automated test script
├── pyproject.toml      # Python dependencies
├── SPEC.md             # Project requirements
├── writeup.md          # This document
├── output/             # Runtime output directory
└── test_results/       # Test results
    ├── trial_1/
    │   ├── 1_workers/
    │   ├── 2_workers/
    │   ├── 4_workers/
    │   ├── 8_workers/
    │   └── 16_workers/
    ├── trial_2/
    └── trial_3/
```

## Appendix B: Running the System

### Local Execution (Without Docker)

```bash
# Terminal 1: Start coordinator
python run_server.py -u http://www.dlsu.edu.ph -t 5

# Terminal 2-N: Start workers
python run_client.py -H localhost -p 9999
```

### Docker Execution

```bash
# Build and run with 4 workers
docker compose up --build --scale worker=4

# Run automated tests (1, 2, 4, 8, 16 workers × 3 trials)
./run_tests.sh
```

### Command-Line Arguments

**Coordinator (`run_server.py`):**
| Argument | Default | Description |
|----------|---------|-------------|
| `-u, --url` | `http://www.dlsu.edu.ph` | Seed URL |
| `-t, --run_minutes` | `1.0` | Crawl duration |
| `-H, --host` | `localhost` | Bind address |
| `-p, --port` | `9999` | Bind port |
| `-o, --output` | `.` | Output directory |

**Worker (`run_client.py`):**
| Argument | Default | Description |
|----------|---------|-------------|
| `-H, --host` | `localhost` | Coordinator host |
| `-p, --port` | `9999` | Coordinator port |
| `-d, --delay` | `0` | Startup delay (seconds) |

---

*Document generated for CSC611M Distributed Programming Project*
*De La Salle University - Computer Technology Department*
