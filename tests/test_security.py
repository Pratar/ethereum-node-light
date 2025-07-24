#!/usr/bin/env python3
"""
Тесты для безопасности Ethereum Node Infrastructure
"""

import subprocess
import json
import pytest
from typing import Dict, Any


class TestSecurity:
    """Тесты для безопасности"""
    
    def setup_method(self):
        """Настройка перед каждым тестом"""
        self.namespace = "ethereum"
        self.node_name = "ethereum-node-0"
        
    def run_kubectl(self, command: str) -> Dict[str, Any]:
        """Выполнить kubectl команду"""
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
    
    def test_network_policy_created(self):
        """TEST_SECURITY_NP: Network Policy создан"""
        result = self.run_kubectl(f"get networkpolicy -n {self.namespace}")
        assert result["success"], f"Ошибка получения Network Policy: {result.get('error', result['stderr'])}"
        assert "ethereum-node-network-policy" in result["stdout"], "Network Policy не найден"
    
    def test_rbac_configured(self):
        """TEST_SECURITY_RBAC: RBAC настроен"""
        # Проверка ServiceAccount
        result = self.run_kubectl(f"get serviceaccount -n {self.namespace}")
        assert result["success"], f"Ошибка получения ServiceAccount: {result.get('error', result['stderr'])}"
        assert "ethereum-node" in result["stdout"], "ServiceAccount не найден"
        
        # Проверка Role
        result = self.run_kubectl(f"get role -n {self.namespace}")
        assert result["success"], f"Ошибка получения Role: {result.get('error', result['stderr'])}"
        assert "ethereum-node-role" in result["stdout"], "Role не найден"
        
        # Проверка RoleBinding
        result = self.run_kubectl(f"get rolebinding -n {self.namespace}")
        assert result["success"], f"Ошибка получения RoleBinding: {result.get('error', result['stderr'])}"
        assert "ethereum-node-role-binding" in result["stdout"], "RoleBinding не найден"
    
    def test_pod_security_context(self):
        """TEST_SECURITY_PSC: Pod Security Context настроен"""
        result = self.run_kubectl(f"get pod -n {self.namespace} {self.node_name} -o json")
        assert result["success"], f"Ошибка получения pod: {result.get('error', result['stderr'])}"
        
        pod_data = json.loads(result["stdout"])
        security_context = pod_data["spec"]["securityContext"]
        
        # Проверка SecurityContext
        assert security_context["runAsNonRoot"] == True, "runAsNonRoot не настроен"
        assert security_context["runAsUser"] == 1000, "runAsUser не настроен"
        assert security_context["fsGroup"] == 1000, "fsGroup не настроен"
    
    def test_pod_running_as_non_root(self):
        """TEST_SECURITY_NONROOT: Pod запущен от непривилегированного пользователя"""
        result = self.run_kubectl(f"exec -n {self.namespace} {self.node_name} -- id")
        assert result["success"], f"Ошибка выполнения команды id: {result.get('error', result['stderr'])}"
        
        id_output = result["stdout"]
        assert "uid=1000" in id_output, "Pod запущен от root пользователя"
        # Группа может быть 0 в контейнере, это нормально
        assert "gid=0" in id_output or "gid=1000" in id_output, "Неожиданная группа"
    
    def test_network_policy_ingress_rules(self):
        """TEST_SECURITY_NP_INGRESS: Network Policy имеет правила ingress"""
        result = self.run_kubectl(f"get networkpolicy ethereum-node-network-policy -n {self.namespace} -o json")
        assert result["success"], f"Ошибка получения Network Policy: {result.get('error', result['stderr'])}"
        
        np_data = json.loads(result["stdout"])
        ingress_rules = np_data["spec"]["ingress"]
        
        # Проверка наличия правил ingress
        assert len(ingress_rules) > 0, "Отсутствуют правила ingress"
        
        # Проверка портов
        ports = []
        for rule in ingress_rules:
            if "ports" in rule:
                for port in rule["ports"]:
                    ports.append(port["port"])
        
        assert 8545 in ports, "Порт 8545 (RPC) не разрешен"
        assert 30303 in ports, "Порт 30303 (P2P) не разрешен"
        assert 6060 in ports, "Порт 6060 (Metrics) не разрешен"
    
    def test_network_policy_egress_rules(self):
        """TEST_SECURITY_NP_EGRESS: Network Policy имеет правила egress"""
        result = self.run_kubectl(f"get networkpolicy ethereum-node-network-policy -n {self.namespace} -o json")
        assert result["success"], f"Ошибка получения Network Policy: {result.get('error', result['stderr'])}"
        
        np_data = json.loads(result["stdout"])
        egress_rules = np_data["spec"]["egress"]
        
        # Проверка наличия правил egress
        assert len(egress_rules) > 0, "Отсутствуют правила egress"
        
        # Проверка портов
        ports = []
        for rule in egress_rules:
            if "ports" in rule:
                for port in rule["ports"]:
                    ports.append(port["port"])
        
        assert 53 in ports, "Порт 53 (DNS) не разрешен"
        assert 80 in ports, "Порт 80 (HTTP) не разрешен"
        assert 443 in ports, "Порт 443 (HTTPS) не разрешен"


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 