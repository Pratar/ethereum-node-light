#!/usr/bin/env python3
"""
Cluster audit fixes test
Checks that main issues were fixed
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

def run_k8sgpt_analyze():
    try:
        result = subprocess.run(
            "k8sgpt analyze --explain",
            shell=True,
            capture_output=True,
            text=True,
            timeout=120
        )
        if result.returncode == 0:
            lines = result.stdout.split('\n')
            problem_count = 0
            for line in lines:
                if line.strip() and line[0].isdigit() and ':' in line:
                    problem_count += 1
            return problem_count
        return -1
    except Exception as e:
        return -1

class TestAuditFixes:
    def test_kube_state_metrics_service_has_endpoints(self):
        success, output, error = run_kubectl_command(
            "get endpoints kube-state-metrics -n gke-managed-cim -o json"
        )
        assert success, f"Error getting endpoints: {error}"
        data = json.loads(output)
        endpoints = data.get('subsets', [])
        assert len(endpoints) > 0, "Service kube-state-metrics has no endpoints"
        addresses = endpoints[0].get('addresses', [])
        assert len(addresses) > 0, "Service kube-state-metrics has no addresses"

    def test_kube_proxy_service_has_endpoints(self):
        success, output, error = run_kubectl_command(
            "get endpoints kube-proxy -n kube-system -o json"
        )
        assert success, f"Error getting endpoints: {error}"
        data = json.loads(output)
        endpoints = data.get('subsets', [])
        assert len(endpoints) > 0, "Service kube-proxy has no endpoints"

    def test_alertmanager_service_has_endpoints(self):
        success, output, error = run_kubectl_command(
            "get endpoints alertmanager -n monitoring -o json"
        )
        assert success, f"Error getting endpoints: {error}"
        data = json.loads(output)
        endpoints = data.get('subsets', [])
        assert len(endpoints) > 0, "Service alertmanager has no endpoints"

    def test_envoy_gateway_metrics_service_has_endpoints(self):
        success, output, error = run_kubectl_command(
            "get endpoints envoy-gateway-metrics-service -n envoy-gateway-system -o json"
        )
        assert success, f"Error getting endpoints: {error}"
        data = json.loads(output)
        endpoints = data.get('subsets', [])
        assert len(endpoints) > 0, "Service envoy-gateway-metrics-service has no endpoints"

    def test_istiod_pdb_is_healthy(self):
        success, output, error = run_kubectl_command(
            "get pdb istiod -n istio-system -o json"
        )
        assert success, f"Error getting PDB: {error}"
        data = json.loads(output)
        conditions = data.get('status', {}).get('conditions', [])
        disruption_allowed = False
        for condition in conditions:
            if condition.get('type') == 'DisruptionAllowed':
                disruption_allowed = condition.get('status') == 'True'
                break
        current_healthy = data.get('status', {}).get('currentHealthy', 0)
        expected_pods = data.get('status', {}).get('expectedPods', 0)
        assert current_healthy > 0, "PDB istiod has no healthy pods"
        assert current_healthy == expected_pods, "PDB istiod has unexpected number of pods"

    def test_ethereum_nodes_are_running(self):
        success, output, error = run_kubectl_command(
            "get pods -n ethereum -l app=ethereum-node -o json"
        )
        assert success, f"Ошибка получения подов: {error}"
        data = json.loads(output)
        pods = data.get('items', [])
        assert len(pods) >= 3, f"Недостаточно подов Ethereum: {len(pods)}"
        for pod in pods:
            status = pod.get('status', {})
            phase = status.get('phase')
            assert phase == 'Running', f"Под {pod['metadata']['name']} не в состоянии Running: {phase}"
            ready = False
            for condition in status.get('conditions', []):
                if condition.get('type') == 'Ready':
                    ready = condition.get('status') == 'True'
                    break
            assert ready, f"Под {pod['metadata']['name']} не готов"

    def test_cert_manager_certificates_are_ready(self):
        success, output, error = run_kubectl_command(
            "get certificates -n ethereum -o json"
        )
        assert success, f"Ошибка получения сертификатов: {error}"
        data = json.loads(output)
        certificates = data.get('items', [])
        assert len(certificates) > 0, "Нет сертификатов в namespace ethereum"
        for cert in certificates:
            conditions = cert.get('status', {}).get('conditions', [])
            ready = False
            for condition in conditions:
                if condition.get('type') == 'Ready':
                    ready = condition.get('status') == 'True'
                    break
            assert ready, f"Сертификат {cert['metadata']['name']} не готов"

    def test_grafana_dashboard_directory_exists(self):
        success, output, error = run_kubectl_command(
            "exec -n monitoring prometheus-grafana-5c4dddb4b7-vdvmz -c grafana -- ls -la /var/lib/grafana/dashboards"
        )
        assert success, f"Директория дашбордов не существует: {error}"

    def test_system_services_have_correct_labels(self):
        services_to_check = [
            ('kube-system', 'kube-controller-manager', 'component', 'kube-controller-manager'),
            ('kube-system', 'kube-scheduler', 'component', 'kube-scheduler'),
            ('kube-system', 'kube-proxy', 'k8s-app', 'kube-proxy'),
            ('kube-system', 'etcd', 'component', 'etcd'),
        ]
        for namespace, service_name, label_key, label_value in services_to_check:
            success, output, error = run_kubectl_command(
                f"get service {service_name} -n {namespace} -o json"
            )
            assert success, f"Ошибка получения сервиса {service_name}: {error}"
            data = json.loads(output)
            labels = data.get('metadata', {}).get('labels', {})
            assert labels.get(label_key) == label_value, f"Сервис {service_name} не имеет правильный лейбл {label_key}={label_value}"

    def test_k8sgpt_issues_reduced(self):
        problem_count = run_k8sgpt_analyze()
        assert problem_count > 0, "Не удалось получить количество проблем"
        assert problem_count < 60, f"Слишком много проблем k8sgpt: {problem_count}"
        print(f"Количество проблем k8sgpt: {problem_count}")

    def test_ethereum_load_balancing_still_works(self):
        success, output, error = run_kubectl_command(
            "get service ethereum-node-loadbalancer -n ethereum -o json"
        )
        assert success, f"Ошибка получения LoadBalancer: {error}"
        data = json.loads(output)
        external_ips = data.get('status', {}).get('loadBalancer', {}).get('ingress', [])
        assert len(external_ips) > 0, "LoadBalancer не имеет внешних IP"
        success, output, error = run_kubectl_command(
            "get endpoints ethereum-node-loadbalancer -n ethereum -o json"
        )
        assert success, f"Ошибка получения endpoints: {error}"
        data = json.loads(output)
        endpoints = data.get('subsets', [])
        assert len(endpoints) > 0, "LoadBalancer не имеет endpoints"
        addresses = endpoints[0].get('addresses', [])
        assert len(addresses) >= 3, f"LoadBalancer имеет недостаточно адресов: {len(addresses)}"

    def test_hpa_is_configured(self):
        success, output, error = run_kubectl_command(
            "get hpa ethereum-node-hpa -n ethereum -o json"
        )
        assert success, f"Ошибка получения HPA: {error}"
        data = json.loads(output)
        spec = data.get('spec', {})
        assert spec.get('minReplicas') == 3, "HPA имеет неправильное minReplicas"
        assert spec.get('maxReplicas') == 5, "HPA имеет неправильное maxReplicas"
        metrics = spec.get('metrics', [])
        assert len(metrics) >= 2, "HPA должен иметь метрики CPU и памяти"

    def test_cluster_overall_health(self):
        critical_namespaces = ['ethereum', 'monitoring', 'istio-system']
        for namespace in critical_namespaces:
            success, output, error = run_kubectl_command(
                f"get pods -n {namespace} --field-selector=status.phase!=Running -o json"
            )
            assert success, f"Ошибка проверки подов в {namespace}: {error}"
            data = json.loads(output)
            non_running_pods = data.get('items', [])
            problematic_pods = []
            for pod in non_running_pods:
                phase = pod.get('status', {}).get('phase')
                if phase not in ['Completed', 'Succeeded']:
                    problematic_pods.append(pod)
            assert len(problematic_pods) == 0, f"Есть проблемные поды в {namespace}: {[p['metadata']['name'] for p in problematic_pods]}"

if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 