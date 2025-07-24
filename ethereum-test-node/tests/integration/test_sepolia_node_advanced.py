#!/usr/bin/env python3
"""
Advanced integration tests for Sepolia Ethereum node
"""

import pytest
import requests
import json
import time
import os
import sys
from typing import Dict, Any, List

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))

class TestSepoliaNodeAdvanced:
    RPC_URL = "http://localhost:8545"
    HEADERS = {"Content-Type": "application/json"}
    SEPOLIA_CHAIN_ID = 11155111
    TEST_DATA = {
        "valid_address": "0x742d35Cc6634C0532925a3b8D4C9db96C4b4d8b6",
        "contract_address": "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D",
        "test_transaction": {
            "from": "0x742d35Cc6634C0532925a3b8D4C9db96C4b4d8b6",
            "to": "0x742d35Cc6634C0532925a3b8D4C9db96C4b4d8b6",
            "value": "0x0",
            "gas": "0x5208"
        }
    }
    def make_request(self, method: str, params: List[Any] = None) -> Dict[str, Any]:
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
    def test_sync_status_detailed(self):
        result = self.make_request("eth_syncing")
        sync_status = result["result"]
        assert sync_status is False or isinstance(sync_status, dict), "Invalid sync status"
        if isinstance(sync_status, dict):
            assert "currentBlock" in sync_status, "Missing currentBlock in sync status"
            assert "highestBlock" in sync_status, "Missing highestBlock in sync status"
            current = int(sync_status["currentBlock"], 16)
            highest = int(sync_status["highestBlock"], 16)
            assert current <= highest, "Current block cannot exceed highest block"
    def test_block_info_comprehensive(self):
        block_num_result = self.make_request("eth_blockNumber")
        block_number = int(block_num_result["result"], 16)
        result = self.make_request("eth_getBlockByNumber", [hex(block_number), False])
        block_info = result["result"]
        required_fields = ["hash", "number", "timestamp", "transactions"]
        for field in required_fields:
            assert field in block_info, f"Missing required field: {field}"
        assert int(block_info["number"], 16) == block_number, "Block number mismatch"
        timestamp = int(block_info["timestamp"], 16)
        current_time = int(time.time())
        assert abs(current_time - timestamp) < 3600, "Block timestamp too old"
    def test_balance_validation(self):
        address = self.TEST_DATA["valid_address"]
        result = self.make_request("eth_getBalance", [address, "latest"])
        balance_wei = int(result["result"], 16)
        balance_eth = balance_wei / (10**18)
        assert balance_wei >= 0, "Balance cannot be negative"
        assert balance_eth >= 0, "ETH balance cannot be negative"
        assert balance_wei < 10**30, "Balance seems unreasonably high"
    def test_transaction_info(self):
        block_result = self.make_request("eth_getBlockByNumber", ["latest", True])
        block = block_result["result"]
        if block["transactions"]:
            tx_hash = block["transactions"][0]["hash"]
            result = self.make_request("eth_getTransactionByHash", [tx_hash])
            tx_info = result["result"]
            required_tx_fields = ["hash", "from", "to", "value", "gas", "gasPrice"]
            for field in required_tx_fields:
                assert field in tx_info, f"Missing transaction field: {field}"
            assert tx_info["hash"] == tx_hash, "Transaction hash mismatch"
    def test_gas_estimation(self):
        tx_data = self.TEST_DATA["test_transaction"]
        result = self.make_request("eth_estimateGas", [tx_data])
        estimated_gas = int(result["result"], 16)
        assert estimated_gas > 0, "Gas estimation should be positive"
        assert estimated_gas < 10**7, "Gas estimation seems too high"
        gas_price_result = self.make_request("eth_gasPrice")
        gas_price = int(gas_price_result["result"], 16)
        assert gas_price > 0, "Gas price should be positive"
        assert gas_price < 10**20, "Gas price seems unreasonably high"
    def test_contract_code(self):
        contract_address = self.TEST_DATA["contract_address"]
        result = self.make_request("eth_getCode", [contract_address, "latest"])
        contract_code = result["result"]
        assert contract_code != "0x", "Contract should have code"
        assert len(contract_code) > 2, "Contract code should be longer than 0x"
        assert contract_code.startswith("0x"), "Contract code should start with 0x"
        assert all(c in "0123456789abcdef" for c in contract_code[2:].lower()), "Invalid hex format"
    def test_event_logs(self):
        latest_result = self.make_request("eth_blockNumber")
        latest_block = int(latest_result["result"], 16)
        filter_params = {
            "fromBlock": hex(latest_block - 100),
            "toBlock": hex(latest_block),
            "topics": []
        }
        result = self.make_request("eth_getLogs", [filter_params])
        logs = result["result"]
        assert isinstance(logs, list), "Logs should be a list"
        if logs:
            log = logs[0]
            required_log_fields = ["address", "topics", "data", "blockNumber", "transactionHash"]
            for field in required_log_fields:
                assert field in log, f"Missing log field: {field}"
    def test_network_info(self):
        version_result = self.make_request("net_version")
        network_version = version_result["result"]
        assert network_version == str(self.SEPOLIA_CHAIN_ID), f"Wrong network version: {network_version}"
        chain_id_result = self.make_request("eth_chainId")
        chain_id = int(chain_id_result["result"], 16)
        assert chain_id == self.SEPOLIA_CHAIN_ID, f"Wrong chain ID: {chain_id}"
        client_result = self.make_request("web3_clientVersion")
        client_version = client_result["result"]
        assert len(client_version) > 0, "Client version should not be empty"
    def test_performance_metrics(self):
        start_time = time.time()
        for _ in range(5):
            self.make_request("eth_blockNumber")
        end_time = time.time()
        total_time = end_time - start_time
        avg_time = total_time / 5
        assert avg_time < 2.0, f"Average response time too high: {avg_time}s"
        assert avg_time > 0.0, "Response time should be positive"
    def test_error_handling(self):
        result = self.make_request("invalid_method")
        assert "error" in result, "Should return error for invalid method"
        assert result["error"]["code"] == -32601, "Should return method not found error"
        result = self.make_request("eth_getBalance", ["invalid_address"])
        assert "error" in result, "Should return error for invalid address"
    def test_api_compatibility(self):
        standard_methods = [
            "eth_blockNumber",
            "eth_chainId", 
            "eth_gasPrice",
            "net_version",
            "web3_clientVersion"
        ]
        for method in standard_methods:
            result = self.make_request(method)
            assert "result" in result or "error" in result, f"Method {method} should return result or error"
    def test_security_measures(self):
        response = requests.options(self.RPC_URL, headers=self.HEADERS)
        assert "Access-Control-Allow-Origin" in response.headers, "CORS headers should be present"
        test_response = requests.post(self.RPC_URL, json={"jsonrpc": "2.0", "method": "eth_chainId", "id": 1})
        assert "application/json" in test_response.headers.get("Content-Type", ""), "Should return JSON content type"

if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 