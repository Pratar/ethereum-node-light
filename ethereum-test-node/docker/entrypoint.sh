#!/bin/bash
set -e

# Function to log messages
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1"
}

# Function to check if geth is available
check_geth() {
    if ! command -v geth &> /dev/null; then
        log "ERROR: geth not found in PATH"
        exit 1
    fi
    log "geth version: $(geth version)"
}

# Function to start geth with configuration
start_geth() {
    log "Starting Ethereum node..."
    
    # Clean up any existing lock files
    rm -f /data/geth/LOCK
    
    # Default arguments for test node
    GETH_ARGS=(
        "--syncmode=${ETHEREUM_SYNC_MODE:-snap}"
        "--maxpeers=${ETHEREUM_MAX_PEERS:-10}"
        "--http"
        "--http.addr=0.0.0.0"
        "--http.port=${ETHEREUM_HTTP_PORT:-8545}"
        "--http.api=eth,net,web3,personal,debug"
        "--http.corsdomain=*"
        "--http.vhosts=*"
        "--metrics"
        "--metrics.addr=0.0.0.0"
        "--metrics.port=${ETHEREUM_METRICS_PORT:-6060}"
        "--verbosity=3"
        "--datadir=/data"
        "--cache=512"
    )
    
    # Add Sepolia configuration if using Sepolia network
    if [[ "${ETHEREUM_NETWORK_ID}" == "11155111" ]]; then
        # Clear old data if it exists and is from mainnet
        if [[ -f "/data/geth/chaindata/CURRENT" ]]; then
            log "Clearing old mainnet data for Sepolia..."
            rm -rf /data/geth/chaindata/*
            rm -rf /data/geth/chaindata/ancient/*
        fi
        # Use Sepolia configuration with proper sync settings
        GETH_ARGS+=(
            "--sepolia"
            "--syncmode=snap"
            "--discovery.dns=enrtree://AOGECG2SPND25EEF4J5TQ3BCJ9SRXQ6VJUS24JUNQJYFBCLMLMLG@sepolia.ethdisco.net"
            "--http.api=eth,net,web3,personal,debug"
            "--maxpeers=50"
            "--cache=1024"
        )
    fi
    
    # Add WebSocket if enabled
    if [[ "${ETHEREUM_WS_ENABLED:-false}" == "true" ]]; then
        GETH_ARGS+=(
            "--ws"
            "--ws.addr=0.0.0.0"
            "--ws.port=${ETHEREUM_WS_PORT:-8546}"
            "--ws.api=eth,net,web3"
            "--ws.origins=*"
        )
    fi
    
    # Add P2P port if specified
    if [[ -n "${ETHEREUM_P2P_PORT}" ]]; then
        GETH_ARGS+=("--port=${ETHEREUM_P2P_PORT}")
    fi
    
    log "Starting geth with args: ${GETH_ARGS[*]}"
    
    # Start geth
    exec geth "${GETH_ARGS[@]}"
}

# Main execution
main() {
    log "Ethereum Test Node starting..."
    
    # Check prerequisites
    check_geth
    
    # Create directories if they don't exist
    mkdir -p /data /config /logs
    
    # Start geth
    start_geth
}

# Run main function
main "$@" 