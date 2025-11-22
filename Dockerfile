FROM python:3.13-slim

WORKDIR /app

# Install dependencies
RUN pip install --no-cache-dir pyro5 requests networkx beautifulsoup4

# Copy application files
COPY node.py coordinator.py client.py run_server.py run_client.py ./

# Default command (can be overridden in docker-compose)
CMD ["python", "run_server.py"]
