#!/usr/bin/env python3
"""
Test for checking external access to services via Gateway API
"""

import pytest
import requests
import time

class TestExternalAccess:
    """Tests for checking external access"""

    def test_ethereum_gateway_access(self):
        """Check access to Ethereum Gateway"""
        url = "http://localhost:8080/eth"
        try:
            response = requests.get(url, timeout=10)
            assert response.status_code == 200, "Ethereum Gateway is not accessible"
        except Exception as e:
            pytest.fail(f"Error accessing Ethereum Gateway: {e}")

    def test_grafana_gateway_access(self):
        """Check access to Grafana Gateway"""
        url = "http://localhost:8080/grafana"
        try:
            response = requests.get(url, timeout=10)
            assert response.status_code == 200, "Grafana Gateway is not accessible"
        except Exception as e:
            pytest.fail(f"Error accessing Grafana Gateway: {e}")

    def test_prometheus_gateway_access(self):
        """Check access to Prometheus Gateway"""
        url = "http://localhost:8080/prometheus"
        try:
            response = requests.get(url, timeout=10)
            assert response.status_code == 200, "Prometheus Gateway is not accessible"
        except Exception as e:
            pytest.fail(f"Error accessing Prometheus Gateway: {e}") 