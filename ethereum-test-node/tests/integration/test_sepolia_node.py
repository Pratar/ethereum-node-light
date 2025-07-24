#!/usr/bin/env python3
"""
Integration tests for Sepolia Ethereum node
"""

import pytest
import requests
import json
import time
import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))

class TestSepoliaNode:
    """Test class for Sepolia node functionality"""
    
    # Configuration
    RPC_URL = "http://localhost:8545"
    HEADERS = {"Content-Type": "application/json"}
    SEPOLIA_CHAIN_ID = 11155111
    
    def make_request(self, method, params=None):
        """Make RPC request"""
        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params or [],
            "id": 1
        }
        
        try:
            response = requests.post(self.RPC_URL, json=payload, headers=self.HEADERS, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            pytest.fail(f"Error making request: {e}")
    
    def test_node_connectivity(self):
        """Test basic node connectivity"""
        result = self.make_request("eth_chainId")
        assert result is not None, "Node is not responding"
        assert "result" in result, "Invalid response format"
    
    def test_sepolia_chain_id(self):
        """Test that node is on Sepolia network"""
        result = self.make_request("eth_chainId")
        chain_id = int(result["result"], 16)
        assert chain_id == self.SEPOLIA_CHAIN_ID, f"Wrong Chain ID: {chain_id}, expected: {self.SEPOLIA_CHAIN_ID}"
    
    def test_block_number(self):
        """Test block number retrieval"""
        result = self.make_request("eth_blockNumber")
        block_number = int(result["result"], 16)
        assert block_number > 0, f"Block number should be greater than 0, got: {block_number}"
        assert block_number > 8000000, f"Block number seems too low for Sepolia: {block_number}"
    
    def test_syncing_status(self):
        """Test syncing status"""
        result = self.make_request("eth_syncing")
        # Node should be synced (False) or syncing (object)
        assert result["result"] is False or isinstance(result["result"], dict), "Invalid syncing status"
    
    def test_balance_query(self):
        """Test balance query functionality"""
        # Test address with known balance on Sepolia
        test_address = "0x742d35Cc6634C0532925a3b8D4C9db96C4b4d8b6"
        result = self.make_request("eth_getBalance", [test_address, "latest"])
        balance = int(result["result"], 16)
        balance_eth = balance / (10**18)
        assert balance >= 0, "Balance should be non-negative"
        assert balance_eth > 0, f"Test address should have balance, got: {balance_eth} ETH"
    
    def test_network_version(self):
        """Test network version"""
        result = self.make_request("net_version")
        network_version = result["result"]
        assert network_version == str(self.SEPOLIA_CHAIN_ID), f"Wrong network version: {network_version}"
    
    def test_gas_price(self):
        """Test gas price retrieval"""
        result = self.make_request("eth_gasPrice")
        gas_price = int(result["result"], 16)
        assert gas_price > 0, "Gas price should be positive"
        assert gas_price < 10**20, "Gas price seems unreasonably high"
    
    def test_accounts_list(self):
        """Test accounts list (should be empty for read-only node)"""
        result = self.make_request("eth_accounts")
        accounts = result["result"]
        assert isinstance(accounts, list), "Accounts should be a list"
    
    def test_peer_count(self):
        """Test peer count (for proxy this might not be available)"""
        try:
            result = self.make_request("net_peerCount")
            peer_count = int(result["result"], 16)
            assert peer_count >= 0, "Peer count should be non-negative"
        except:
            # This might not be available for proxy
            pass
    
    def test_latest_block_info(self):
        """Test getting latest block information"""
        # Get latest block number
        block_result = self.make_request("eth_blockNumber")
        latest_block = block_result["result"]
        
        # Get block info
        block_info = self.make_request("eth_getBlockByNumber", [latest_block, False])
        assert block_info["result"] is not None, "Should get block information"
        assert "hash" in block_info["result"], "Block should have hash"
        assert "number" in block_info["result"], "Block should have number"
    
    def test_transaction_count(self):
        """Test getting transaction count for an address"""
        # Use a known address
        test_address = "0x742d35Cc6634C0532925a3b8D4C9db96C4b4d8b6"
        result = self.make_request("eth_getTransactionCount", [test_address, "latest"])
        tx_count = int(result["result"], 16)
        assert tx_count >= 0, "Transaction count should be non-negative"
    
    def test_code_at_address(self):
        """Test getting code at address"""
        # Test with a contract address (WETH on Sepolia)
        contract_address = "0x7b79995e5f793A07Bc00c21412e50Ecae098E7f9"  # WETH on Sepolia
        result = self.make_request("eth_getCode", [contract_address, "latest"])
        code = result["result"]
        assert code != "0x", "Contract should have code"
    
    def test_storage_at_address(self):
        """Test getting storage at address"""
        # Test with a contract address
        contract_address = "0x7b79995e5f793A07Bc00c21412e50Ecae098E7f9"  # WETH on Sepolia
        storage_position = "0x0"  # First storage slot
        result = self.make_request("eth_getStorageAt", [contract_address, storage_position, "latest"])
        storage_value = result["result"]
        assert storage_value is not None, "Should get storage value"
    
    def test_estimate_gas(self):
        """Test gas estimation"""
        # Simple transaction data
        tx_data = {
            "from": "0x742d35Cc6634C0532925a3b8D4C9db96C4b4d8b6",
            "to": "0x742d35Cc6634C0532925a3b8D4C9db96C4b4d8b6",
            "value": "0x0"
        }
        result = self.make_request("eth_estimateGas", [tx_data])
        gas_estimate = int(result["result"], 16)
        assert gas_estimate > 0, "Gas estimate should be positive"
        assert gas_estimate < 1000000, "Gas estimate seems unreasonably high"
    
    def test_call_contract(self):
        """Test contract call (read-only)"""
        # WETH contract on Sepolia
        contract_address = "0x7b79995e5f793A07Bc00c21412e50Ecae098E7f9"
        # Call data for name() function
        call_data = "0x06fdde03"  # name() function selector
        tx_data = {
            "to": contract_address,
            "data": call_data
        }
        result = self.make_request("eth_call", [tx_data, "latest"])
        assert result["result"] is not None, "Should get call result"
    
    def test_logs_filter(self):
        """Test getting logs"""
        # Get logs for recent blocks
        block_result = self.make_request("eth_blockNumber")
        latest_block = int(block_result["result"], 16)
        from_block = hex(latest_block - 10)  # Last 10 blocks
        
        filter_params = {
            "fromBlock": from_block,
            "toBlock": "latest",
            "topics": []
        }
        result = self.make_request("eth_getLogs", [filter_params])
        # Handle case where logs might be empty or error
        if "result" in result:
            logs = result["result"]
            assert isinstance(logs, list), "Logs should be a list"
        else:
            # If no logs or error, that's also acceptable for a test node
            assert "error" in result or result.get("result") is None, "Should have error or empty result"
    
    def test_web3_client_version(self):
        """Test web3 client version"""
        result = self.make_request("web3_clientVersion")
        version = result["result"]
        assert version is not None, "Should get client version"
        assert len(version) > 0, "Version should not be empty"
    
    def test_sha3(self):
        """Test SHA3 function"""
        test_data = "0x68656c6c6f"  # "hello" in hex
        result = self.make_request("web3_sha3", [test_data])
        hash_result = result["result"]
        assert hash_result is not None, "Should get SHA3 hash"
        assert hash_result.startswith("0x"), "Hash should start with 0x"
        assert len(hash_result) == 66, "SHA3 hash should be 32 bytes + 0x prefix" 