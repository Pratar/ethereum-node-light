#!/usr/bin/env python3
"""
Test for checking cluster problem fixes after k8sgpt audit
"""

import pytest
import subprocess
import json

def run_kubectl_command(command):
    try:
        result = subprocess.run(
            f"kubectl {command}",
            shell=True,
            capture_output=True,
            text=True,
            timeout=30
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "Timeout"
    except Exception as e:
        return False, "", str(e)

class TestClusterAuditFix:
    def test_ethereum_httproute_service_exists(self):
        # Проверяем существование сервиса
        success, output, error = run_kubectl_command(
            "get service ethereum-node -n ethereum -o json"
        )
        assert success, f"Ошибка получения сервиса: {error}"
        data = json.loads(output)
        assert data["metadata"]["name"] == "ethereum-node"
        # Проверяем HTTPRoute
        success, output, error = run_kubectl_command(
            "get httproute ethereum-route -n ethereum -o json"
        )
        assert success, f"Ошибка получения HTTPRoute: {error}"
        httproute = json.loads(output)
        for rule in httproute['spec']['rules']:
            for backend in rule['backendRefs']:
                assert backend['name'] == 'ethereum-node'
                assert backend['port'] == 8545 or backend['port'] == 6060

    def test_kube_state_metrics_service_exists(self):
        success, output, error = run_kubectl_command(
            "get service kube-state-metrics -n gke-managed-cim -o json"
        )
        assert success, f"Сервис kube-state-metrics не найден: {error}"
        data = json.loads(output)
        assert data["metadata"]["name"] == "kube-state-metrics"
        assert data["spec"].get("selector") is not None

    def test_system_services_exist(self):
        system_services = [
            ("kube-controller-manager", "kube-system"),
            ("kube-scheduler", "kube-system"),
            ("kube-proxy", "kube-system"),
            ("etcd", "kube-system")
        ]
        for service_name, namespace in system_services:
            success, output, error = run_kubectl_command(
                f"get service {service_name} -n {namespace} -o json"
            )
            assert success, f"Сервис {service_name} в namespace {namespace} не найден: {error}"

    def test_grafana_dashboard_configmap_exists(self):
        success, output, error = run_kubectl_command(
            "get configmap ethereum-dashboard -n monitoring -o json"
        )
        assert success, f"ConfigMap ethereum-dashboard не найден: {error}"
        data = json.loads(output)
        assert "ethereum-dashboard.json" in data.get("data", {})

    def test_vpa_admission_controller_running(self):
        success, output, error = run_kubectl_command(
            "get pods -n kube-system -l app=vpa-admission-controller -o json"
        )
        assert success, f"Ошибка при проверке VPA admission controller: {error}"
        data = json.loads(output)
        assert len(data["items"]) > 0
        for pod in data["items"]:
            assert pod["status"]["phase"] == "Running"
            for container in pod["status"].get("containerStatuses", []):
                assert container["ready"]

    def test_ethereum_node_metrics_endpoint_accessible(self):
        success, output, error = run_kubectl_command(
            "get pods -n ethereum -l app=ethereum-node -o json"
        )
        assert success, f"Ошибка при проверке Ethereum ноды: {error}"
        data = json.loads(output)
        assert len(data["items"]) > 0
        for pod in data["items"]:
            assert pod["status"]["phase"] == "Running"
            for container in pod["status"].get("containerStatuses", []):
                assert container["ready"]

    def test_cluster_overall_health(self):
        success, output, error = run_kubectl_command(
            "get pods --all-namespaces -o json"
        )
        assert success, f"Ошибка при проверке состояния кластера: {error}"
        data = json.loads(output)
        failed_pods = []
        for pod in data["items"]:
            if pod["status"]["phase"] in ["Failed", "CrashLoopBackOff", "Error"]:
                failed_pods.append(f"{pod['metadata']['namespace']}/{pod['metadata']['name']}")
        assert len(failed_pods) <= 5, f"Слишком много неработающих подов: {failed_pods}"

if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 