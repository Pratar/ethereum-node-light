#!/usr/bin/env python3
"""
Tests for monitoring system
"""

import pytest
import requests
import subprocess
import json
import time

class TestMonitoring:
    """Tests for monitoring system"""

    def test_prometheus_metrics_endpoint(self):
        """Check Prometheus metrics endpoint"""
        url = "http://localhost:9090/metrics"
        response = requests.get(url, timeout=10)
        assert response.status_code == 200, "Prometheus metrics endpoint is not accessible"
        assert "go_memstats" in response.text, "Prometheus metrics missing expected data"

    def test_grafana_dashboard_access(self):
        """Check Grafana dashboard access"""
        url = "http://localhost:3000/login"
        response = requests.get(url, timeout=10)
        assert response.status_code == 200, "Grafana dashboard is not accessible"
        assert "Grafana" in response.text, "Grafana dashboard page missing expected content"

    def test_node_exporter_metrics(self):
        """Check Node Exporter metrics endpoint"""
        url = "http://localhost:9100/metrics"
        response = requests.get(url, timeout=10)
        assert response.status_code == 200, "Node Exporter metrics endpoint is not accessible"
        assert "node_cpu_seconds_total" in response.text, "Node Exporter metrics missing expected data" 