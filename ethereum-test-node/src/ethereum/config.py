"""
Ethereum Node Configuration

Module for managing Ethereum test node configuration.
"""

import os
from dataclasses import dataclass
from typing import Optional, Dict, Any
import yaml


@dataclass
class EthereumConfig:
    """Ethereum node configuration"""
    
    # Main parameters
    network: str = "testnet"
    sync_mode: str = "light"
    max_peers: int = 10
    max_pend_peers: int = 5
    cache: int = 512
    block_limit: int = 100
    
    # HTTP API
    http_enabled: bool = True
    http_addr: str = "0.0.0.0"
    http_port: int = 8545
    http_api: str = "eth,net,web3,personal,debug"
    http_cors_domain: str = "*"
    
    # WebSocket API
    ws_enabled: bool = False
    ws_addr: str = "0.0.0.0"
    ws_port: int = 8546
    ws_api: str = "eth,net,web3"
    ws_origins: str = "*"
    
    # Paths
    data_dir: str = "/data"
    config_dir: str = "/config"
    
    # Monitoring
    metrics_enabled: bool = True
    metrics_port: int = 6060
    
    def __post_init__(self):
        """Validate configuration after initialization"""
        self._validate_network()
        self._validate_sync_mode()
        self._validate_block_limit()
    
    def _validate_network(self):
        """Validate network"""
        valid_networks = ["mainnet", "testnet", "dev", "goerli", "sepolia"]
        if self.network not in valid_networks:
            raise ValueError(f"Unsupported network: {self.network}. Supported: {valid_networks}")
    
    def _validate_sync_mode(self):
        """Validate sync mode"""
        valid_modes = ["light", "fast", "full"]
        if self.sync_mode not in valid_modes:
            raise ValueError(f"Unsupported sync mode: {self.sync_mode}. Supported: {valid_modes}")
    
    def _validate_block_limit(self):
        """Validate block limit"""
        if self.block_limit <= 0:
            raise ValueError("Block limit must be greater than 0")
        if self.block_limit > 10000:
            raise ValueError("Block limit cannot exceed 10000")
    
    @classmethod
    def from_env(cls) -> "EthereumConfig":
        """Create configuration from environment variables"""
        return cls(
            network=os.getenv("ETHEREUM_NETWORK", "testnet"),
            sync_mode=os.getenv("ETHEREUM_SYNC_MODE", "light"),
            max_peers=int(os.getenv("ETHEREUM_MAX_PEERS", "10")),
            max_pend_peers=int(os.getenv("ETHEREUM_MAX_PEND_PEERS", "5")),
            cache=int(os.getenv("ETHEREUM_CACHE", "512")),
            block_limit=int(os.getenv("ETHEREUM_BLOCK_LIMIT", "100")),
            http_enabled=os.getenv("ETHEREUM_HTTP_ENABLED", "true").lower() == "true",
            http_addr=os.getenv("ETHEREUM_HTTP_ADDR", "0.0.0.0"),
            http_port=int(os.getenv("ETHEREUM_HTTP_PORT", "8545")),
            http_api=os.getenv("ETHEREUM_HTTP_API", "eth,net,web3,personal,debug"),
            http_cors_domain=os.getenv("ETHEREUM_HTTP_CORS_DOMAIN", "*"),
            ws_enabled=os.getenv("ETHEREUM_WS_ENABLED", "false").lower() == "true",
            ws_addr=os.getenv("ETHEREUM_WS_ADDR", "0.0.0.0"),
            ws_port=int(os.getenv("ETHEREUM_WS_PORT", "8546")),
            ws_api=os.getenv("ETHEREUM_WS_API", "eth,net,web3"),
            ws_origins=os.getenv("ETHEREUM_WS_ORIGINS", "*"),
            data_dir=os.getenv("ETHEREUM_DATA_DIR", "/data"),
            config_dir=os.getenv("ETHEREUM_CONFIG_DIR", "/config"),
            metrics_enabled=os.getenv("ETHEREUM_METRICS_ENABLED", "true").lower() == "true",
            metrics_port=int(os.getenv("ETHEREUM_METRICS_PORT", "6060")),
        )
    
    @classmethod
    def from_file(cls, file_path: str) -> "EthereumConfig":
        """Create configuration from file"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Configuration file not found: {file_path}")
        
        with open(file_path, 'r') as f:
            config_data = yaml.safe_load(f)
        
        return cls(**config_data)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "network": self.network,
            "sync_mode": self.sync_mode,
            "max_peers": self.max_peers,
            "max_pend_peers": self.max_pend_peers,
            "cache": self.cache,
            "block_limit": self.block_limit,
            "http_enabled": self.http_enabled,
            "http_addr": self.http_addr,
            "http_port": self.http_port,
            "http_api": self.http_api,
            "http_cors_domain": self.http_cors_domain,
            "ws_enabled": self.ws_enabled,
            "ws_addr": self.ws_addr,
            "ws_port": self.ws_port,
            "ws_api": self.ws_api,
            "ws_origins": self.ws_origins,
            "data_dir": self.data_dir,
            "config_dir": self.config_dir,
            "metrics_enabled": self.metrics_enabled,
            "metrics_port": self.metrics_port,
        }
    
    def to_yaml(self) -> str:
        """Convert to YAML"""
        return yaml.dump(self.to_dict(), default_flow_style=False)
    
    def save_to_file(self, file_path: str):
        """Save configuration to file"""
        with open(file_path, 'w') as f:
            f.write(self.to_yaml())
    
    def get_geth_args(self) -> list:
        """Get command line arguments for Geth"""
        args = []
        
        # Main parameters
        args.extend(["--networkid", self._get_network_id()])
        args.extend(["--syncmode", self.sync_mode])
        args.extend(["--maxpeers", str(self.max_peers)])
        args.extend(["--maxpendpeers", str(self.max_pend_peers)])
        args.extend(["--cache", str(self.cache)])
        args.extend(["--datadir", self.data_dir])
        
        # HTTP API
        if self.http_enabled:
            args.extend(["--http"])
            args.extend(["--http.addr", self.http_addr])
            args.extend(["--http.port", str(self.http_port)])
            args.extend(["--http.api", self.http_api])
            args.extend(["--http.corsdomain", self.http_cors_domain])
        
        # WebSocket API
        if self.ws_enabled:
            args.extend(["--ws"])
            args.extend(["--ws.addr", self.ws_addr])
            args.extend(["--ws.port", str(self.ws_port)])
            args.extend(["--ws.api", self.ws_api])
            args.extend(["--ws.origins", self.ws_origins])
        
        # Metrics
        if self.metrics_enabled:
            args.extend(["--metrics"])
            args.extend(["--metrics.addr", "0.0.0.0"])
            args.extend(["--metrics.port", str(self.metrics_port)])
        
        return args
    
    def _get_network_id(self) -> str:
        """Get network ID"""
        network_ids = {
            "mainnet": "1",
            "testnet": "5",  # Goerli
            "goerli": "5",
            "sepolia": "11155111",
            "dev": "1337"
        }
        return network_ids.get(self.network, "5")
    
    def __str__(self) -> str:
        """String representation of configuration"""
        return f"EthereumConfig(network={self.network}, sync_mode={self.sync_mode}, block_limit={self.block_limit})"
    
    def __repr__(self) -> str:
        """Debug representation"""
        return self.__str__() 