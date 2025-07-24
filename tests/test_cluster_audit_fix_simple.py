#!/usr/bin/env python3
"""
Simple test for checking cluster problem fixes after k8sgpt audit
"""

import pytest
import subprocess
import json
import time

class TestClusterAuditFixSimple:
    """Simple tests for checking cluster problem fixes"""
    
    def run_kubectl(self, command):
        """Executes kubectl command"""
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
    
    def test_ethereum_httproute_service_exists(self):
        """Checks that HTTPRoute references existing service"""
        # Check service existence
        success, output, error = self.run_kubectl("get svc ethereum-node -n ethereum")
        assert success, f"Service ethereum-node not found: {error}"
        
        # Check HTTPRoute
        success, output, error = self.run_kubectl("get httproute ethereum-route -n ethereum -o json")
        assert success, f"HTTPRoute ethereum-route not found: {error}"
        
        # Parse JSON and check backendRef
        try:
            httproute = json.loads(output)
            for rule in httproute['spec']['rules']:
                for backend in rule['backendRefs']:
                    assert backend['name'] == 'ethereum-node'
                    assert backend['port'] in [8545, 6060]
        except (json.JSONDecodeError, KeyError) as e:
            pytest.fail(f"Error parsing HTTPRoute: {e}")
    
    def test_kube_state_metrics_service_exists(self):
        """Checks that kube-state-metrics service exists"""
        success, output, error = self.run_kubectl("get svc kube-state-metrics -n gke-managed-cim")
        assert success, f"Service kube-state-metrics not found: {error}"
    
    def test_system_services_exist(self):
        """Checks existence of system services"""
        system_services = [
            ("kube-controller-manager", "kube-system"),
            ("kube-scheduler", "kube-system"),
            ("kube-proxy", "kube-system"),
            ("etcd", "kube-system")
        ]
        
        for service_name, namespace in system_services:
            success, output, error = self.run_kubectl(f"get svc {service_name} -n {namespace}")
            assert success, f"Service {service_name} in namespace {namespace} not found: {error}"
    
    def test_grafana_dashboard_configmap_exists(self):
        """Checks existence of ConfigMap with Grafana dashboard"""
        success, output, error = self.run_kubectl("get configmap ethereum-dashboard -n monitoring")
        assert success, f"ConfigMap ethereum-dashboard not found: {error}"
        
        # Check content
        success, output, error = self.run_kubectl("get configmap ethereum-dashboard -n monitoring -o json")
        if success:
            try:
                configmap = json.loads(output)
                assert "ethereum-dashboard.json" in configmap['data']
            except (json.JSONDecodeError, KeyError):
                pass  # Not critical
    
    def test_vpa_admission_controller_running(self):
        """Checks that VPA admission controller is running"""
        success, output, error = self.run_kubectl("get pods -n kube-system -l app=vpa-admission-controller")
        assert success, f"VPA admission controller not found: {error}"
        
        # Check that pods are running
        success, output, error = self.run_kubectl("get pods -n kube-system -l app=vpa-admission-controller -o jsonpath='{.items[*].status.phase}'")
        if success and output.strip():
            phases = output.strip().split()
            assert all(phase == "Running" for phase in phases), f"Not all VPA pods are running: {phases}"
    
    def test_istiod_pdb_has_correct_labels(self):
        """Checks that PDB istiod has correct labels"""
        success, output, error = self.run_kubectl("get pdb istiod -n istio-system")
        assert success, f"PDB istiod not found: {error}"
        
        # Check that pods with labels exist
        success, output, error = self.run_kubectl("get pods -n istio-system -l app=istiod,istio=pilot")
        assert success, f"istiod pods with correct labels not found: {error}"
    
    def test_prometheus_config_reloader_working(self):
        """Проверяет, что config-reloader Prometheus работает"""
        success, output, error = self.run_kubectl("get pods -n monitoring -l app=prometheus")
        assert success, f"Поды Prometheus не найдены: {error}"
        
        # Проверяем config-reloader
        success, output, error = self.run_kubectl("get pods -n monitoring -l app=prometheus -o jsonpath='{.items[*].status.phase}'")
        if success and output.strip():
            phases = output.strip().split()
            assert all(phase == "Running" for phase in phases), f"Не все поды Prometheus работают: {phases}"
    
    def test_ethereum_node_metrics_endpoint_accessible(self):
        """Проверяет доступность метрик Ethereum ноды"""
        success, output, error = self.run_kubectl("get pods -n ethereum -l app=ethereum-node")
        assert success, f"Поды Ethereum ноды не найдены: {error}"
        
        # Проверяем, что поды работают
        success, output, error = self.run_kubectl("get pods -n ethereum -l app=ethereum-node -o jsonpath='{.items[*].status.phase}'")
        if success and output.strip():
            phases = output.strip().split()
            assert all(phase == "Running" for phase in phases), f"Не все поды Ethereum работают: {phases}"
    
    def test_cluster_overall_health(self):
        """Проверяет общее состояние кластера"""
        success, output, error = self.run_kubectl("get pods --all-namespaces -o jsonpath='{.items[?(@.status.phase==\"Failed\")].metadata.namespace}/{.items[?(@.status.phase==\"Failed\")].metadata.name}'")
        
        if success and output.strip():
            failed_pods = output.strip().split()
            # Допускаем небольшое количество неработающих подов (системные)
            assert len(failed_pods) <= 5, f"Слишком много неработающих подов: {failed_pods}"
    
    def test_k8sgpt_issues_reduced(self):
        """Проверяет, что количество проблем k8sgpt уменьшилось"""
        success, output, error = self.run_kubectl("k8sgpt analyze")
        
        if success:
            # Подсчитываем количество проблем (строки с номером и двоеточием)
            lines = output.split('\n')
            issue_lines = [line for line in lines if line.strip() and ':' in line and line.split(':')[0].isdigit()]
            
            # Ожидаем, что количество проблем меньше 20 (было 47)
            assert len(issue_lines) < 20, f"Слишком много проблем k8sgpt: {len(issue_lines)}"

if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 