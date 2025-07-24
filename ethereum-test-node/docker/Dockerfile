# Ethereum Test Node Dockerfile
# Simple and reliable configuration

FROM ethereum/client-go:stable

# Install additional tools
RUN apk add --no-cache \
    python3 \
    py3-pip \
    curl \
    wget \
    bash \
    jq

# Create application directory
WORKDIR /app

# Copy Python requirements and install
COPY requirements.txt .
RUN pip3 install --no-cache-dir --break-system-packages -r requirements.txt

# Copy application files
COPY src/ ./src/
COPY scripts/ ./scripts/

# Create necessary directories
RUN mkdir -p /data /config /logs

# Copy entrypoint script
COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Expose ports
EXPOSE 8545 8546 30303 30303/udp 6060

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:6060/health || exit 1

# Use custom entrypoint
ENTRYPOINT ["/entrypoint.sh"]
