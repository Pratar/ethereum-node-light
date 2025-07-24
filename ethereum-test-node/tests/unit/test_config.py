"""
Unit tests for Ethereum node configuration module
"""

import pytest
import os
import tempfile
import yaml
from unittest.mock import patch

from src.ethereum.config import EthereumConfig


class TestEthereumConfig:
    """Tests for EthereumConfig class"""
    
    def test_default_config(self):
        """Test default configuration"""
        config = EthereumConfig()
        
        assert config.network == "testnet"
        assert config.sync_mode == "light"
        assert config.max_peers == 10
        assert config.block_limit == 100
        assert config.http_enabled is True
        assert config.http_port == 8545
    
    def test_custom_config(self):
        """Test custom configuration"""
        config = EthereumConfig(
            network="mainnet",
            sync_mode="fast",
            max_peers=20,
            block_limit=50,
            http_port=8080
        )
        
        assert config.network == "mainnet"
        assert config.sync_mode == "fast"
        assert config.max_peers == 20
        assert config.block_limit == 50
        assert config.http_port == 8080
    
    def test_invalid_network(self):
        """Test invalid network"""
        with pytest.raises(ValueError, match="Unsupported network"):
            EthereumConfig(network="invalid_network")
    
    def test_invalid_sync_mode(self):
        """Test invalid sync mode"""
        with pytest.raises(ValueError, match="Unsupported sync mode"):
            EthereumConfig(sync_mode="invalid_mode")
    
    def test_invalid_block_limit_zero(self):
        """Test zero block limit"""
        with pytest.raises(ValueError, match="Block limit must be greater than 0"):
            EthereumConfig(block_limit=0)
    
    def test_invalid_block_limit_negative(self):
        """Test negative block limit"""
        with pytest.raises(ValueError, match="Block limit must be greater than 0"):
            EthereumConfig(block_limit=-10)
    
    def test_invalid_block_limit_too_high(self):
        """Test too high block limit"""
        with pytest.raises(ValueError, match="Block limit cannot exceed 10000"):
            EthereumConfig(block_limit=15000)
    
    def test_from_env(self):
        """Test creating configuration from environment variables"""
        env_vars = {
            "ETHEREUM_NETWORK": "mainnet",
            "ETHEREUM_SYNC_MODE": "fast",
            "ETHEREUM_MAX_PEERS": "15",
            "ETHEREUM_BLOCK_LIMIT": "200",
            "ETHEREUM_HTTP_PORT": "9000"
        }
        
        with patch.dict(os.environ, env_vars):
            config = EthereumConfig.from_env()
            
            assert config.network == "mainnet"
            assert config.sync_mode == "fast"
            assert config.max_peers == 15
            assert config.block_limit == 200
            assert config.http_port == 9000
    
    def test_from_env_defaults(self):
        """Test creating configuration from environment variables with default values"""
        with patch.dict(os.environ, {}, clear=True):
            config = EthereumConfig.from_env()
            
            assert config.network == "testnet"
            assert config.sync_mode == "light"
            assert config.max_peers == 10
            assert config.block_limit == 100
    
    def test_from_file(self):
        """Test creating configuration from file"""
        config_data = {
            "network": "sepolia",
            "sync_mode": "light",
            "max_peers": 25,
            "block_limit": 75,
            "http_port": 8546
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            temp_file = f.name
        
        try:
            config = EthereumConfig.from_file(temp_file)
            
            assert config.network == "sepolia"
            assert config.sync_mode == "light"
            assert config.max_peers == 25
            assert config.block_limit == 75
            assert config.http_port == 8546
        finally:
            os.unlink(temp_file)
    
    def test_from_file_not_found(self):
        """Test creating configuration from non-existent file"""
        with pytest.raises(FileNotFoundError):
            EthereumConfig.from_file("/nonexistent/file.yaml")
    
    def test_to_dict(self):
        """Test conversion to dictionary"""
        config = EthereumConfig(
            network="goerli",
            sync_mode="light",
            max_peers=12,
            block_limit=150
        )
        
        config_dict = config.to_dict()
        
        assert config_dict["network"] == "goerli"
        assert config_dict["sync_mode"] == "light"
        assert config_dict["max_peers"] == 12
        assert config_dict["block_limit"] == 150
        assert config_dict["http_enabled"] is True
        assert config_dict["http_port"] == 8545
    
    def test_to_yaml(self):
        """Test conversion to YAML"""
        config = EthereumConfig(
            network="dev",
            sync_mode="full",
            block_limit=50
        )
        
        yaml_str = config.to_yaml()
        config_dict = yaml.safe_load(yaml_str)
        
        assert config_dict["network"] == "dev"
        assert config_dict["sync_mode"] == "full"
        assert config_dict["block_limit"] == 50
    
    def test_save_to_file(self):
        """Test saving configuration to file"""
        config = EthereumConfig(
            network="mainnet",
            sync_mode="fast",
            max_peers=30
        )
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            temp_file = f.name
        
        try:
            config.save_to_file(temp_file)
            
            # Check that file is created and contains correct data
            assert os.path.exists(temp_file)
            
            with open(temp_file, 'r') as f:
                saved_data = yaml.safe_load(f)
            
            assert saved_data["network"] == "mainnet"
            assert saved_data["sync_mode"] == "fast"
            assert saved_data["max_peers"] == 30
        finally:
            os.unlink(temp_file)
    
    def test_get_geth_args(self):
        """Test getting command line arguments for Geth"""
        config = EthereumConfig(
            network="testnet",
            sync_mode="light",
            max_peers=10,
            block_limit=100,
            http_enabled=True,
            http_port=8545,
            ws_enabled=True,
            ws_port=8546,
            metrics_enabled=True,
            metrics_port=6060
        )
        
        args = config.get_geth_args()
        
        # Check main arguments
        assert "--networkid" in args
        assert "5" in args  # ID for testnet
        assert "--syncmode" in args
        assert "light" in args
        assert "--maxpeers" in args
        assert "10" in args
        assert "--datadir" in args
        assert "/data" in args
        
        # Check HTTP arguments
        assert "--http" in args
        assert "--http.addr" in args
        assert "0.0.0.0" in args
        assert "--http.port" in args
        assert "8545" in args
        
        # Check WebSocket arguments
        assert "--ws" in args
        assert "--ws.port" in args
        assert "8546" in args
        
        # Check metrics
        assert "--metrics" in args
        assert "--metrics.port" in args
        assert "6060" in args
    
    def test_get_geth_args_http_disabled(self):
        """Test Geth arguments with HTTP disabled"""
        config = EthereumConfig(
            http_enabled=False,
            ws_enabled=False,
            metrics_enabled=False
        )
        
        args = config.get_geth_args()
        
        # Check that HTTP arguments are missing
        assert "--http" not in args
        assert "--http.addr" not in args
        assert "--http.port" not in args
        
        # Check that WebSocket arguments are missing
        assert "--ws" not in args
        assert "--ws.port" not in args
        
        # Check that metrics are missing
        assert "--metrics" not in args
        assert "--metrics.port" not in args
    
    def test_get_network_id(self):
        """Test getting network ID"""
        config = EthereumConfig()
        
        # Test different networks
        test_cases = [
            ("mainnet", "1"),
            ("testnet", "5"),
            ("goerli", "5"),
            ("sepolia", "11155111"),
            ("dev", "1337")
        ]
        
        for network, expected_id in test_cases:
            config.network = network
            args = config.get_geth_args()
            
            # Find --networkid index and check next argument
            networkid_index = args.index("--networkid")
            assert args[networkid_index + 1] == expected_id
    
    def test_string_representation(self):
        """Test string representation"""
        config = EthereumConfig(
            network="mainnet",
            sync_mode="fast",
            block_limit=200
        )
        
        config_str = str(config)
        assert "EthereumConfig" in config_str
        assert "network=mainnet" in config_str
        assert "sync_mode=fast" in config_str
        assert "block_limit=200" in config_str
    
    def test_repr_representation(self):
        """Test debug representation"""
        config = EthereumConfig(network="testnet")
        
        config_repr = repr(config)
        assert config_repr == str(config) 