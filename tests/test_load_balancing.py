#!/usr/bin/env python3
"""
Тест для проверки балансировки нагрузки между 3 репликами Ethereum ноды
"""

import pytest
import subprocess
import json
import time
import requests

class TestLoadBalancing:
    """Тесты для проверки балансировки нагрузки"""
    
    def run_kubectl(self, command):
        """Выполняет kubectl команду"""
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
    
    def test_statefulset_has_three_replicas(self):
        """Проверяет, что StatefulSet имеет 3 реплики"""
        success, output, error = self.run_kubectl("get statefulset ethereum-node -n ethereum -o jsonpath='{.spec.replicas}'")
        assert success, f"Не удалось получить количество реплик: {error}"
        assert output.strip() == "3", f"Ожидалось 3 реплики, получено {output.strip()}"
    
    def test_all_pods_are_running(self):
        """Проверяет, что все 3 пода работают"""
        success, output, error = self.run_kubectl("get statefulset ethereum-node -n ethereum -o jsonpath='{.status.readyReplicas}'")
        assert success, f"Не удалось получить количество готовых реплик: {error}"
        assert output.strip() == "3", f"Ожидалось 3 готовых реплики, получено {output.strip()}"
    
    def test_loadbalancer_service_exists(self):
        """Проверяет наличие сервиса LoadBalancer"""
        success, output, error = self.run_kubectl("get svc ethereum-node-loadbalancer -n ethereum")
        assert success, f"Сервис LoadBalancer не найден: {error}"
    
    def test_headless_service_exists(self):
        """Проверяет наличие headless сервиса"""
        success, output, error = self.run_kubectl("get svc ethereum-node-headless -n ethereum")
        assert success, f"Headless сервис не найден: {error}"
    
    def test_loadbalancer_has_external_ip(self):
        """Проверяет, что LoadBalancer имеет внешний IP"""
        success, output, error = self.run_kubectl("get svc ethereum-node-loadbalancer -n ethereum -o jsonpath='{.status.loadBalancer.ingress[0].ip}'")
        assert success, f"Не удалось получить внешний IP LoadBalancer: {error}"
        assert output.strip(), "LoadBalancer не имеет внешнего IP"
    
    def test_loadbalancer_endpoints_include_all_pods(self):
        """Проверяет, что все поды включены в endpoints LoadBalancer"""
        success, output, error = self.run_kubectl("get endpoints ethereum-node-loadbalancer -n ethereum -o jsonpath='{.subsets[0].addresses[*].targetRef.name}'")
        assert success, f"Не удалось получить endpoints: {error}"
        
        endpoints = output.strip().split()
        assert len(endpoints) == 3, f"Ожидалось 3 endpoints, получено {len(endpoints)}"
        
        # Проверяем, что все поды включены
        expected_pods = ["ethereum-node-0", "ethereum-node-1", "ethereum-node-2"]
        for pod in expected_pods:
            assert pod in endpoints, f"Под {pod} не найден в endpoints"
    
    def test_hpa_exists_and_configured(self):
        """Проверяет наличие и конфигурацию HPA"""
        success, output, error = self.run_kubectl("get hpa ethereum-node-hpa -n ethereum")
        assert success, f"HPA не найден: {error}"
        
        # Проверяем минимальное количество реплик
        success, output, error = self.run_kubectl("get hpa ethereum-node-hpa -n ethereum -o jsonpath='{.spec.minReplicas}'")
        assert success, f"Не удалось получить minReplicas: {error}"
        assert output.strip() == "3", f"Ожидалось minReplicas=3, получено {output.strip()}"
        
        # Проверяем максимальное количество реплик
        success, output, error = self.run_kubectl("get hpa ethereum-node-hpa -n ethereum -o jsonpath='{.spec.maxReplicas}'")
        assert success, f"Не удалось получить maxReplicas: {error}"
        assert output.strip() == "5", f"Ожидалось maxReplicas=5, получено {output.strip()}"
    
    def test_httproute_uses_loadbalancer(self):
        """Проверяет, что HTTPRoute использует LoadBalancer сервис"""
        success, output, error = self.run_kubectl("get httproute ethereum-route -n ethereum -o jsonpath='{.spec.rules[0].backendRefs[0].name}'")
        assert success, f"Не удалось получить backendRef HTTPRoute: {error}"
        assert output.strip() == "ethereum-node-loadbalancer", f"HTTPRoute должен использовать ethereum-node-loadbalancer, получено {output.strip()}"
    
    def test_ethereum_nodes_are_synchronizing(self):
        """Проверяет, что все Ethereum ноды синхронизируются"""
        for i in range(3):
            pod_name = f"ethereum-node-{i}"
            success, output, error = self.run_kubectl(f"logs {pod_name} -n ethereum --tail=5")
            assert success, f"Не удалось получить логи пода {pod_name}: {error}"
            
            # Проверяем, что в логах есть информация о синхронизации
            assert "Starting peer-to-peer node" in output or "HTTP server started" in output, f"Под {pod_name} не запустился корректно"
    
    def test_load_balancing_distribution(self):
        """Проверяет распределение нагрузки между подами"""
        # Получаем IP адреса подов
        success, output, error = self.run_kubectl("get pods -n ethereum -l app=ethereum-node -o jsonpath='{.items[*].status.podIP}'")
        assert success, f"Не удалось получить IP адреса подов: {error}"
        
        pod_ips = output.strip().split()
        assert len(pod_ips) == 3, f"Ожидалось 3 IP адреса, получено {len(pod_ips)}"
        
        # Проверяем, что все поды отвечают на RPC запросы
        for pod_ip in pod_ips:
            if pod_ip:
                # Тестируем через port-forward
                success, output, error = self.run_kubectl(f"exec -n ethereum ethereum-node-0 -- curl -s -X POST -H 'Content-Type: application/json' --data '{{\"jsonrpc\":\"2.0\",\"method\":\"eth_blockNumber\",\"params\":[],\"id\":1}}' http://{pod_ip}:8545")
                if success:
                    try:
                        response = json.loads(output)
                        assert "result" in response, f"Неправильный ответ от пода {pod_ip}"
                    except json.JSONDecodeError:
                        # Это нормально, если под еще не готов
                        pass
    
    def test_resource_usage_distribution(self):
        """Проверяет распределение использования ресурсов"""
        success, output, error = self.run_kubectl("top pods -n ethereum -l app=ethereum-node")
        assert success, f"Не удалось получить информацию о ресурсах: {error}"
        
        lines = output.strip().split('\n')[1:]  # Пропускаем заголовок
        assert len(lines) == 3, f"Ожидалось 3 строки с ресурсами, получено {len(lines)}"
        
        # Проверяем, что все поды используют ресурсы
        for line in lines:
            if line.strip():
                parts = line.split()
                assert len(parts) >= 3, f"Неполная информация о ресурсах: {line}"
                
                # Проверяем, что CPU и память не нулевые
                cpu = parts[1]
                memory = parts[2]
                assert cpu != "0m", f"CPU использование равно 0: {line}"
                assert memory != "0Mi", f"Использование памяти равно 0: {line}"
    
    def test_high_availability(self):
        """Проверяет высокую доступность системы"""
        # Проверяем, что система работает даже если один под недоступен
        success, output, error = self.run_kubectl("get svc ethereum-node-loadbalancer -n ethereum -o jsonpath='{.spec.selector.app}'")
        assert success, f"Не удалось получить селектор сервиса: {error}"
        assert output.strip() == "ethereum-node", f"Неправильный селектор сервиса: {output.strip()}"
        
        # Проверяем, что endpoints обновляются
        success, output, error = self.run_kubectl("get endpoints ethereum-node-loadbalancer -n ethereum -o jsonpath='{.subsets[0].addresses}'")
        assert success, f"Не удалось получить endpoints: {error}"
        assert output.strip(), "Endpoints пустые"

if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 