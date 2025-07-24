import pytest
import subprocess
import json
import time

class TestMonitoringGateway:
    """Tests for Gateway API access to monitoring"""
    
    def test_grafana_gateway_exists(self):
        """Check that Gateway for Grafana exists"""
        result = subprocess.run([
            'kubectl', 'get', 'gateway', 'grafana-gateway', '-n', 'monitoring'
        ], capture_output=True, text=True)
        
        assert result.returncode == 0, "Gateway grafana-gateway не найден"
    
    def test_grafana_gateway_configuration(self):
        """Проверка конфигурации Gateway для Grafana"""
        result = subprocess.run([
            'kubectl', 'get', 'gateway', 'grafana-gateway', '-n', 'monitoring', '-o', 'json'
        ], capture_output=True, text=True)
        
        assert result.returncode == 0, f"Ошибка получения Gateway: {result.stderr}"
        
        gw = json.loads(result.stdout)
        
        # Проверяем GatewayClass
        assert gw['spec']['gatewayClassName'] == 'istio', "Неверный GatewayClass"
        
        # Проверяем listeners
        assert len(gw['spec']['listeners']) == 2, "Должно быть 2 listener'а"
        
        # Проверяем HTTP listener
        http_listener = None
        https_listener = None
        for listener in gw['spec']['listeners']:
            if listener['name'] == 'http':
                http_listener = listener
            elif listener['name'] == 'https':
                https_listener = listener
        
        assert http_listener is not None, "HTTP listener не найден"
        assert http_listener['port'] == 80, "Неверный HTTP порт"
        assert http_listener['protocol'] == 'HTTP', "Неверный HTTP протокол"
        
        assert https_listener is not None, "HTTPS listener не найден"
        assert https_listener['port'] == 443, "Неверный HTTPS порт"
        assert https_listener['protocol'] == 'HTTPS', "Неверный HTTPS протокол"
    
    def test_grafana_httproute_exists(self):
        """Проверка что HTTPRoute для Grafana существует"""
        result = subprocess.run([
            'kubectl', 'get', 'httproute', 'grafana-route', '-n', 'monitoring'
        ], capture_output=True, text=True)
        
        assert result.returncode == 0, "HTTPRoute grafana-route не найден"
    
    def test_grafana_httproute_configuration(self):
        """Проверка конфигурации HTTPRoute для Grafana"""
        result = subprocess.run([
            'kubectl', 'get', 'httproute', 'grafana-route', '-n', 'monitoring', '-o', 'json'
        ], capture_output=True, text=True)
        
        assert result.returncode == 0, f"Ошибка получения HTTPRoute: {result.stderr}"
        
        route = json.loads(result.stdout)
        
        # Проверяем parentRefs
        assert len(route['spec']['parentRefs']) > 0, "Отсутствуют parentRefs"
        parent_ref = route['spec']['parentRefs'][0]
        assert parent_ref['name'] == 'grafana-gateway', "Неверный parent gateway"
        
        # Проверяем hostnames
        assert len(route['spec']['hostnames']) > 0, "Отсутствуют hostnames"
        assert 'grafana.example.com' in route['spec']['hostnames'], "Неверный hostname"
        
        # Проверяем rules
        assert len(route['spec']['rules']) == 1, "Должно быть 1 правило"
        
        rule = route['spec']['rules'][0]
        assert len(rule['matches']) > 0, "Отсутствуют matches"
        assert rule['matches'][0]['path']['type'] == 'PathPrefix', "Неверный тип пути"
        assert rule['matches'][0]['path']['value'] == '/', "Неверный путь"
        
        # Проверяем backendRefs
        assert len(rule['backendRefs']) > 0, "Отсутствуют backendRefs"
        backend_ref = rule['backendRefs'][0]
        assert backend_ref['name'] == 'prometheus-grafana', "Неверный backend service"
        assert backend_ref['port'] == 80, "Неверный backend порт"
    
    def test_prometheus_gateway_exists(self):
        """Проверка что Gateway для Prometheus существует"""
        result = subprocess.run([
            'kubectl', 'get', 'gateway', 'prometheus-gateway', '-n', 'monitoring'
        ], capture_output=True, text=True)
        
        assert result.returncode == 0, "Gateway prometheus-gateway не найден"
    
    def test_prometheus_gateway_configuration(self):
        """Проверка конфигурации Gateway для Prometheus"""
        result = subprocess.run([
            'kubectl', 'get', 'gateway', 'prometheus-gateway', '-n', 'monitoring', '-o', 'json'
        ], capture_output=True, text=True)
        
        assert result.returncode == 0, f"Ошибка получения Gateway: {result.stderr}"
        
        gw = json.loads(result.stdout)
        
        # Проверяем GatewayClass
        assert gw['spec']['gatewayClassName'] == 'istio', "Неверный GatewayClass"
        
        # Проверяем listeners
        assert len(gw['spec']['listeners']) == 2, "Должно быть 2 listener'а"
        
        # Проверяем HTTP listener
        http_listener = None
        https_listener = None
        for listener in gw['spec']['listeners']:
            if listener['name'] == 'http':
                http_listener = listener
            elif listener['name'] == 'https':
                https_listener = listener
        
        assert http_listener is not None, "HTTP listener не найден"
        assert http_listener['port'] == 80, "Неверный HTTP порт"
        assert http_listener['protocol'] == 'HTTP', "Неверный HTTP протокол"
        
        assert https_listener is not None, "HTTPS listener не найден"
        assert https_listener['port'] == 443, "Неверный HTTPS порт"
        assert https_listener['protocol'] == 'HTTPS', "Неверный HTTPS протокол"
    
    def test_prometheus_httproute_exists(self):
        """Проверка что HTTPRoute для Prometheus существует"""
        result = subprocess.run([
            'kubectl', 'get', 'httproute', 'prometheus-route', '-n', 'monitoring'
        ], capture_output=True, text=True)
        
        assert result.returncode == 0, "HTTPRoute prometheus-route не найден"
    
    def test_prometheus_httproute_configuration(self):
        """Проверка конфигурации HTTPRoute для Prometheus"""
        result = subprocess.run([
            'kubectl', 'get', 'httproute', 'prometheus-route', '-n', 'monitoring', '-o', 'json'
        ], capture_output=True, text=True)
        
        assert result.returncode == 0, f"Ошибка получения HTTPRoute: {result.stderr}"
        
        route = json.loads(result.stdout)
        
        # Проверяем parentRefs
        assert len(route['spec']['parentRefs']) > 0, "Отсутствуют parentRefs"
        parent_ref = route['spec']['parentRefs'][0]
        assert parent_ref['name'] == 'prometheus-gateway', "Неверный parent gateway"
        
        # Проверяем hostnames
        assert len(route['spec']['hostnames']) > 0, "Отсутствуют hostnames"
        assert 'prometheus.example.com' in route['spec']['hostnames'], "Неверный hostname"
        
        # Проверяем rules
        assert len(route['spec']['rules']) == 1, "Должно быть 1 правило"
        
        rule = route['spec']['rules'][0]
        assert len(rule['matches']) > 0, "Отсутствуют matches"
        assert rule['matches'][0]['path']['type'] == 'PathPrefix', "Неверный тип пути"
        assert rule['matches'][0]['path']['value'] == '/', "Неверный путь"
        
        # Проверяем backendRefs
        assert len(rule['backendRefs']) > 0, "Отсутствуют backendRefs"
        backend_ref = rule['backendRefs'][0]
        assert backend_ref['name'] == 'prometheus-kube-prometheus-prometheus', "Неверный backend service"
        assert backend_ref['port'] == 9090, "Неверный backend порт"

class TestMonitoringCertificates:
    """Тесты для сертификатов мониторинга"""
    
    def test_grafana_certificate_exists(self):
        """Проверка что Certificate для Grafana существует"""
        result = subprocess.run([
            'kubectl', 'get', 'certificate', 'grafana-tls-cert', '-n', 'monitoring'
        ], capture_output=True, text=True)
        
        assert result.returncode == 0, "Certificate grafana-tls-cert не найден"
    
    def test_grafana_certificate_configuration(self):
        """Проверка конфигурации Certificate для Grafana"""
        result = subprocess.run([
            'kubectl', 'get', 'certificate', 'grafana-tls-cert', '-n', 'monitoring', '-o', 'json'
        ], capture_output=True, text=True)
        
        assert result.returncode == 0, f"Ошибка получения Certificate: {result.stderr}"
        
        cert = json.loads(result.stdout)
        
        # Проверяем secretName
        assert cert['spec']['secretName'] == 'grafana-tls-cert', "Неверный secretName"
        
        # Проверяем issuerRef
        assert cert['spec']['issuerRef']['name'] == 'selfsigned-issuer', "Неверный issuer"
        assert cert['spec']['issuerRef']['kind'] == 'ClusterIssuer', "Неверный kind issuer"
        
        # Проверяем dnsNames
        assert len(cert['spec']['dnsNames']) > 0, "Отсутствуют dnsNames"
        assert 'grafana.example.com' in cert['spec']['dnsNames'], "Неверный dnsName"
    
    def test_prometheus_certificate_exists(self):
        """Проверка что Certificate для Prometheus существует"""
        result = subprocess.run([
            'kubectl', 'get', 'certificate', 'prometheus-tls-cert', '-n', 'monitoring'
        ], capture_output=True, text=True)
        
        assert result.returncode == 0, "Certificate prometheus-tls-cert не найден"
    
    def test_prometheus_certificate_configuration(self):
        """Проверка конфигурации Certificate для Prometheus"""
        result = subprocess.run([
            'kubectl', 'get', 'certificate', 'prometheus-tls-cert', '-n', 'monitoring', '-o', 'json'
        ], capture_output=True, text=True)
        
        assert result.returncode == 0, f"Ошибка получения Certificate: {result.stderr}"
        
        cert = json.loads(result.stdout)
        
        # Проверяем secretName
        assert cert['spec']['secretName'] == 'prometheus-tls-cert', "Неверный secretName"
        
        # Проверяем issuerRef
        assert cert['spec']['issuerRef']['name'] == 'selfsigned-issuer', "Неверный issuer"
        assert cert['spec']['issuerRef']['kind'] == 'ClusterIssuer', "Неверный kind issuer"
        
        # Проверяем dnsNames
        assert len(cert['spec']['dnsNames']) > 0, "Отсутствуют dnsNames"
        assert 'prometheus.example.com' in cert['spec']['dnsNames'], "Неверный dnsName"
    
    def test_monitoring_certificates_status(self):
        """Проверка статуса сертификатов мониторинга"""
        # Ждем немного для генерации сертификатов
        time.sleep(30)
        
        # Проверяем Grafana certificate
        result = subprocess.run([
            'kubectl', 'get', 'certificate', 'grafana-tls-cert', '-n', 'monitoring', '-o', 'json'
        ], capture_output=True, text=True)
        
        assert result.returncode == 0, f"Ошибка получения Certificate: {result.stderr}"
        
        cert = json.loads(result.stdout)
        
        # Проверяем что есть условия
        assert 'status' in cert, "Отсутствует статус"
        assert 'conditions' in cert['status'], "Отсутствуют условия"
        
        # Проверяем что сертификат готов
        ready_condition = None
        for condition in cert['status']['conditions']:
            if condition['type'] == 'Ready':
                ready_condition = condition
                break
        
        assert ready_condition is not None, "Условие Ready не найдено"
        assert ready_condition['status'] == 'True', f"Сертификат Grafana не готов: {ready_condition['message']}"
        
        # Проверяем Prometheus certificate
        result = subprocess.run([
            'kubectl', 'get', 'certificate', 'prometheus-tls-cert', '-n', 'monitoring', '-o', 'json'
        ], capture_output=True, text=True)
        
        assert result.returncode == 0, f"Ошибка получения Certificate: {result.stderr}"
        
        cert = json.loads(result.stdout)
        
        # Проверяем что есть условия
        assert 'status' in cert, "Отсутствует статус"
        assert 'conditions' in cert['status'], "Отсутствуют условия"
        
        # Проверяем что сертификат готов
        ready_condition = None
        for condition in cert['status']['conditions']:
            if condition['type'] == 'Ready':
                ready_condition = condition
                break
        
        assert ready_condition is not None, "Условие Ready не найдено"
        assert ready_condition['status'] == 'True', f"Сертификат Prometheus не готов: {ready_condition['message']}"

class TestMonitoringIntegration:
    """Интеграционные тесты мониторинга"""
    
    def test_monitoring_services_exist(self):
        """Проверка что сервисы мониторинга существуют"""
        # Проверяем Grafana service
        result = subprocess.run([
            'kubectl', 'get', 'svc', 'prometheus-grafana', '-n', 'monitoring'
        ], capture_output=True, text=True)
        
        assert result.returncode == 0, "Сервис prometheus-grafana не найден"
        
        # Проверяем Prometheus service
        result = subprocess.run([
            'kubectl', 'get', 'svc', 'prometheus-kube-prometheus-prometheus', '-n', 'monitoring'
        ], capture_output=True, text=True)
        
        assert result.returncode == 0, "Сервис prometheus-kube-prometheus-prometheus не найден"
    
    def test_monitoring_pods_running(self):
        """Проверка что поды мониторинга запущены"""
        # Проверяем Grafana pod
        result = subprocess.run([
            'kubectl', 'get', 'pods', '-n', 'monitoring', '-l', 'app.kubernetes.io/name=grafana'
        ], capture_output=True, text=True)
        
        assert result.returncode == 0, "Ошибка получения подов Grafana"
        assert 'Running' in result.stdout, "Нет запущенных подов Grafana"
        
        # Проверяем Prometheus pod
        result = subprocess.run([
            'kubectl', 'get', 'pods', '-n', 'monitoring', '-l', 'app.kubernetes.io/name=prometheus'
        ], capture_output=True, text=True)
        
        assert result.returncode == 0, "Ошибка получения подов Prometheus"
        assert 'Running' in result.stdout, "Нет запущенных подов Prometheus"
    
    def test_monitoring_gateway_services(self):
        """Проверка что Gateway сервисы созданы"""
        # Проверяем Grafana Gateway service
        result = subprocess.run([
            'kubectl', 'get', 'svc', 'grafana-gateway-istio', '-n', 'monitoring'
        ], capture_output=True, text=True)
        
        assert result.returncode == 0, "Ошибка получения сервиса Grafana Gateway"
        assert 'LoadBalancer' in result.stdout, "Grafana Gateway сервис не создан"
        
        # Проверяем Prometheus Gateway service
        result = subprocess.run([
            'kubectl', 'get', 'svc', 'prometheus-gateway-istio', '-n', 'monitoring'
        ], capture_output=True, text=True)
        
        assert result.returncode == 0, "Ошибка получения сервиса Prometheus Gateway"
        assert 'LoadBalancer' in result.stdout, "Prometheus Gateway сервис не создан" 