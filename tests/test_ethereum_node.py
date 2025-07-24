#!/usr/bin/env python3
"""
Tests for Ethereum Node Infrastructure & Reliability
Created according to TDD methodology
"""

import subprocess
import json
import time
import requests
import pytest
from typing import Dict, Any, List


class TestEthereumNode:
    """Tests for Ethereum node"""
    
    def setup_method(self):
        """Setup before each test"""
        self.namespace = "ethereum"
        self.node_name = "ethereum-node-0"
        self.rpc_port = 8545
        self.metrics_port = 6060
        
    def run_kubectl(self, command: str) -> Dict[str, Any]:
        """Execute kubectl command"""
        try:
            result = subprocess.run(
                f"kubectl {command}",
                shell=True,
                capture_output=True,
                text=True,
                timeout=30
            )
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Timeout"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def test_ethereum_node_pod_ready(self):
        """TEST_ETH_NODE: Node is running and ready"""
        result = self.run_kubectl(f"get pods -n {self.namespace} {self.node_name} -o json")
        assert result["success"], f"Error getting pod status: {result.get('error', result['stderr'])}"
        
        pod_data = json.loads(result["stdout"])
        pod_status = pod_data["status"]["phase"]
        ready_condition = next(
            (cond for cond in pod_data["status"]["conditions"] if cond["type"] == "Ready"),
            None
        )
        
        assert pod_status == "Running", f"Pod not in Running state: {pod_status}"
        assert ready_condition is not None, "Ready condition not found"
        assert ready_condition["status"] == "True", f"Pod not ready: {ready_condition['message']}"
    
    def test_ethereum_node_chain_id(self):
        """TEST_ETH_NODE: Chain ID is correct (Sepolia)"""
        # Start port-forward
        port_forward = subprocess.Popen(
            f"kubectl port-forward -n {self.namespace} {self.node_name} {self.rpc_port}:{self.rpc_port}",
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        try:
            time.sleep(3)  # Wait for port-forward to start
            
            # Request Chain ID
            payload = {
                "jsonrpc": "2.0",
                "method": "eth_chainId",
                "params": [],
                "id": 1
            }
            
            response = requests.post(
                f"http://localhost:{self.rpc_port}",
                json=payload,
                timeout=10
            )
            
            assert response.status_code == 200, f"HTTP error: {response.status_code}"
            
            data = response.json()
            assert "result" in data, "Missing result field in response"
            
            chain_id = int(data["result"], 16)
            expected_chain_id = 11155111  # Sepolia
            
            assert chain_id == expected_chain_id, f"Invalid Chain ID: {chain_id}, expected: {expected_chain_id}"
            
        finally:
            port_forward.terminate()
            port_forward.wait()
    
    def test_ethereum_node_syncing(self):
        """TEST_ETH_NODE: Нода синхронизируется"""
        port_forward = subprocess.Popen(
            f"kubectl port-forward -n {self.namespace} {self.node_name} {self.rpc_port}:{self.rpc_port}",
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        try:
            time.sleep(5)  # Увеличиваем время ожидания
            
            # Проверка синхронизации с повторными попытками
            payload = {
                "jsonrpc": "2.0",
                "method": "eth_syncing",
                "params": [],
                "id": 1
            }
            
            # Попытка подключения с повторными попытками
            for attempt in range(3):
                try:
                    response = requests.post(
                        f"http://localhost:{self.rpc_port}",
                        json=payload,
                        timeout=10
                    )
                    break
                except requests.exceptions.ConnectionError:
                    if attempt < 2:
                        time.sleep(2)
                        continue
                    else:
                        raise
            
            assert response.status_code == 200, f"HTTP ошибка: {response.status_code}"
            
            data = response.json()
            assert "result" in data, "Отсутствует поле result в ответе"
            
            # Для light sync результат может быть False (уже синхронизирован)
            # или объект с информацией о синхронизации
            syncing_result = data["result"]
            assert isinstance(syncing_result, (bool, dict)), f"Неожиданный тип результата: {type(syncing_result)}"
            
        finally:
            port_forward.terminate()
            port_forward.wait()
    
    def test_ethereum_node_metrics(self):
        """TEST_METRICS: Метрики доступны"""
        port_forward = subprocess.Popen(
            f"kubectl port-forward -n {self.namespace} {self.node_name} {self.metrics_port}:{self.metrics_port}",
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        try:
            time.sleep(5)  # Увеличиваем время ожидания
            
            # Попытка подключения с повторными попытками
            for attempt in range(3):
                try:
                    response = requests.get(
                        f"http://localhost:{self.metrics_port}/debug/metrics",
                        timeout=10
                    )
                    break
                except requests.exceptions.ConnectionError:
                    if attempt < 2:
                        time.sleep(2)
                        continue
                    else:
                        raise
            
            assert response.status_code == 200, f"HTTP ошибка: {response.status_code}"
            assert len(response.text) > 0, "Метрики пустые"
            
            # Проверка наличия ключевых метрик
            metrics_text = response.text
            assert "blobpool" in metrics_text, "Отсутствуют blobpool метрики"
            assert "eth" in metrics_text, "Отсутствуют eth метрики"
            
        finally:
            port_forward.terminate()
            port_forward.wait()
    
    def test_ethereum_node_health_checks(self):
        """TEST_HEALTH_CHECKS: Health checks работают"""
        result = self.run_kubectl(f"describe pod -n {self.namespace} {self.node_name}")
        assert result["success"], f"Ошибка получения описания pod: {result.get('error', result['stderr'])}"
        
        describe_output = result["stdout"]
        
        # Проверка наличия liveness probe
        assert "Liveness:" in describe_output, "Отсутствует Liveness probe"
        
        # Проверка наличия readiness probe
        assert "Readiness:" in describe_output, "Отсутствует Readiness probe"
        
        # Проверка что probes настроены на правильный endpoint
        assert "/debug/metrics" in describe_output, "Probes не настроены на /debug/metrics"
    
    def test_ethereum_node_pvc(self):
        """TEST_BACKUP: PVC создан и примонтирован"""
        result = self.run_kubectl(f"get pvc -n {self.namespace} -o json")
        assert result["success"], f"Ошибка получения PVC: {result.get('error', result['stderr'])}"
        
        pvc_data = json.loads(result["stdout"])
        assert len(pvc_data["items"]) > 0, "PVC не найден"
        
        pvc = pvc_data["items"][0]
        pvc_status = pvc["status"]["phase"]
        assert pvc_status == "Bound", f"PVC не привязан: {pvc_status}"
        
        # Проверка размера PVC
        storage_class = pvc["spec"]["storageClassName"]
        assert storage_class == "standard", f"Неверный Storage Class: {storage_class}"
    
    def test_ethereum_node_service(self):
        """TEST_IAC_K8S: Service создан"""
        result = self.run_kubectl(f"get service -n {self.namespace} -o json")
        assert result["success"], f"Ошибка получения Service: {result.get('error', result['stderr'])}"
        
        service_data = json.loads(result["stdout"])
        assert len(service_data["items"]) > 0, "Service не найден"
        
        # Ищем сервис ethereum-node
        service = None
        for item in service_data["items"]:
            if item["metadata"]["name"] == "ethereum-node":
                service = item
                break
        
        assert service is not None, "Сервис ethereum-node не найден"
        service_name = service["metadata"]["name"]
        assert service_name == "ethereum-node", f"Неверное имя Service: {service_name}"
        
        # Проверка портов
        ports = service["spec"]["ports"]
        port_numbers = [port["port"] for port in ports]
        assert 8545 in port_numbers, "Порт 8545 (RPC) не найден"
        assert 30303 in port_numbers, "Порт 30303 (P2P) не найден"
        assert 6060 in port_numbers, "Порт 6060 (Metrics) не найден"


class TestInfrastructure:
    """Тесты для инфраструктуры"""
    
    def test_gke_cluster_ready(self):
        """TEST_ENV_CLOUD: GKE кластер готов"""
        result = subprocess.run(
            "gcloud container clusters list --format=json",
            shell=True,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        assert result.returncode == 0, f"Ошибка получения списка кластеров: {result.stderr}"
        
        clusters_data = json.loads(result.stdout)
        assert len(clusters_data) > 0, "Кластеры не найдены"
        
        # Проверка статуса кластера
        cluster = clusters_data[0]
        status = cluster["status"]
        assert status == "RUNNING", f"Кластер не в состоянии RUNNING: {status}"
    
    def test_kubernetes_resources(self):
        """TEST_IAC_K8S: Все ресурсы созданы"""
        namespace = "ethereum"
        
        resources = [
            "pods",
            "services", 
            "statefulsets",
            "persistentvolumeclaims",
            "serviceaccounts"
        ]
        
        for resource in resources:
            result = subprocess.run(
                f"kubectl get {resource} -n {namespace}",
                shell=True,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            assert result.returncode == 0, f"Ошибка получения {resource}: {result.stderr}"
            assert "No resources found" not in result.stdout, f"Ресурс {resource} не найден"


class TestScaling:
    """Тесты для масштабирования"""
    
    def test_hpa_created(self):
        """TEST_SCALING_HPA: HPA создан"""
        result = subprocess.run(
            "kubectl get hpa -n ethereum",
            shell=True,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        assert result.returncode == 0, f"Ошибка получения HPA: {result.stderr}"
        assert "ethereum-node-hpa" in result.stdout, "HPA не найден"
    
    def test_vpa_created(self):
        """TEST_SCALING_VPA: VPA создан"""
        result = subprocess.run(
            "kubectl get vpa -n ethereum",
            shell=True,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        assert result.returncode == 0, f"Ошибка получения VPA: {result.stderr}"
        assert "ethereum-node-vpa" in result.stdout, "VPA не найден"
    
    def test_metrics_server_ready(self):
        """TEST_SCALING_METRICS: Metrics Server готов"""
        result = subprocess.run(
            "kubectl get pods -n kube-system | grep metrics-server",
            shell=True,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        assert result.returncode == 0, f"Ошибка получения Metrics Server: {result.stderr}"
        assert "Running" in result.stdout, "Metrics Server не запущен"


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 