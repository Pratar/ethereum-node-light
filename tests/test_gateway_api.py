import pytest
import subprocess
import json
import time

class TestGatewayAPI:
    """Тесты для Gateway API"""
    
    def test_gateway_class_exists(self):
        """Проверка что GatewayClass существует"""
        result = subprocess.run([
            'kubectl', 'get', 'gatewayclass', 'istio'
        ], capture_output=True, text=True)
        
        assert result.returncode == 0, "GatewayClass istio не найден"
    
    def test_gateway_class_configuration(self):
        """Проверка конфигурации GatewayClass"""
        result = subprocess.run([
            'kubectl', 'get', 'gatewayclass', 'istio', '-o', 'json'
        ], capture_output=True, text=True)
        
        assert result.returncode == 0, f"Ошибка получения GatewayClass: {result.stderr}"
        
        gc = json.loads(result.stdout)
        
        # Проверяем контроллер
        assert gc['spec']['controllerName'] == 'istio.io/gateway-controller', "Неверный контроллер"
        assert gc['spec']['description'] == 'Istio Gateway API controller', "Неверное описание"
    
    def test_gateway_exists(self):
        """Проверка что Gateway существует"""
        result = subprocess.run([
            'kubectl', 'get', 'gateway', 'ethereum-gateway', '-n', 'ethereum'
        ], capture_output=True, text=True)
        
        assert result.returncode == 0, "Gateway ethereum-gateway не найден"
    
    def test_gateway_configuration(self):
        """Проверка конфигурации Gateway"""
        result = subprocess.run([
            'kubectl', 'get', 'gateway', 'ethereum-gateway', '-n', 'ethereum', '-o', 'json'
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
    
    def test_httproute_exists(self):
        """Проверка что HTTPRoute существует"""
        result = subprocess.run([
            'kubectl', 'get', 'httproute', 'ethereum-route', '-n', 'ethereum'
        ], capture_output=True, text=True)
        
        assert result.returncode == 0, "HTTPRoute ethereum-route не найден"
    
    def test_httproute_configuration(self):
        """Проверка конфигурации HTTPRoute"""
        result = subprocess.run([
            'kubectl', 'get', 'httproute', 'ethereum-route', '-n', 'ethereum', '-o', 'json'
        ], capture_output=True, text=True)
        
        assert result.returncode == 0, f"Ошибка получения HTTPRoute: {result.stderr}"
        
        route = json.loads(result.stdout)
        
        # Проверяем parentRefs
        assert len(route['spec']['parentRefs']) > 0, "Отсутствуют parentRefs"
        parent_ref = route['spec']['parentRefs'][0]
        assert parent_ref['name'] == 'ethereum-gateway', "Неверный parent gateway"
        
        # Проверяем hostnames
        assert len(route['spec']['hostnames']) > 0, "Отсутствуют hostnames"
        assert 'ethereum.example.com' in route['spec']['hostnames'], "Неверный hostname"
        
        # Проверяем rules
        assert len(route['spec']['rules']) == 2, "Должно быть 2 правила"
        
        # Проверяем первое правило (RPC)
        rpc_rule = route['spec']['rules'][0]
        assert len(rpc_rule['matches']) > 0, "Отсутствуют matches в RPC правиле"
        assert rpc_rule['matches'][0]['path']['type'] == 'PathPrefix', "Неверный тип пути"
        assert rpc_rule['matches'][0]['path']['value'] == '/', "Неверный путь"
        
        # Проверяем backendRefs
        assert len(rpc_rule['backendRefs']) > 0, "Отсутствуют backendRefs"
        backend_ref = rpc_rule['backendRefs'][0]
        assert backend_ref['name'] == 'ethereum-node-service', "Неверный backend service"
        assert backend_ref['port'] == 8545, "Неверный backend порт"
        
        # Проверяем второе правило (debug)
        debug_rule = route['spec']['rules'][1]
        assert len(debug_rule['matches']) > 0, "Отсутствуют matches в debug правиле"
        assert debug_rule['matches'][0]['path']['type'] == 'PathPrefix', "Неверный тип пути"
        assert debug_rule['matches'][0]['path']['value'] == '/debug', "Неверный путь"

class TestCertificate:
    """Тесты для сертификатов"""
    
    def test_cluster_issuer_exists(self):
        """Проверка что ClusterIssuer существует"""
        result = subprocess.run([
            'kubectl', 'get', 'clusterissuer', 'selfsigned-issuer'
        ], capture_output=True, text=True)
        
        assert result.returncode == 0, "ClusterIssuer selfsigned-issuer не найден"
    
    def test_certificate_exists(self):
        """Проверка что Certificate существует"""
        result = subprocess.run([
            'kubectl', 'get', 'certificate', 'ethereum-tls-cert', '-n', 'ethereum'
        ], capture_output=True, text=True)
        
        assert result.returncode == 0, "Certificate ethereum-tls-cert не найден"
    
    def test_certificate_configuration(self):
        """Проверка конфигурации Certificate"""
        result = subprocess.run([
            'kubectl', 'get', 'certificate', 'ethereum-tls-cert', '-n', 'ethereum', '-o', 'json'
        ], capture_output=True, text=True)
        
        assert result.returncode == 0, f"Ошибка получения Certificate: {result.stderr}"
        
        cert = json.loads(result.stdout)
        
        # Проверяем secretName
        assert cert['spec']['secretName'] == 'ethereum-tls-cert', "Неверный secretName"
        
        # Проверяем issuerRef
        assert cert['spec']['issuerRef']['name'] == 'selfsigned-issuer', "Неверный issuer"
        assert cert['spec']['issuerRef']['kind'] == 'ClusterIssuer', "Неверный kind issuer"
        
        # Проверяем dnsNames
        assert len(cert['spec']['dnsNames']) > 0, "Отсутствуют dnsNames"
        assert 'ethereum.example.com' in cert['spec']['dnsNames'], "Неверный dnsName"
    
    def test_certificate_status(self):
        """Проверка статуса Certificate"""
        # Ждем немного для генерации сертификата
        time.sleep(30)
        
        result = subprocess.run([
            'kubectl', 'get', 'certificate', 'ethereum-tls-cert', '-n', 'ethereum', '-o', 'json'
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
        assert ready_condition['status'] == 'True', f"Сертификат не готов: {ready_condition['message']}"

class TestGatewayIntegration:
    """Интеграционные тесты Gateway API"""
    
    def test_gateway_status(self):
        """Проверка статуса Gateway"""
        result = subprocess.run([
            'kubectl', 'get', 'gateway', 'ethereum-gateway', '-n', 'ethereum', '-o', 'json'
        ], capture_output=True, text=True)
        
        assert result.returncode == 0, f"Ошибка получения Gateway: {result.stderr}"
        
        gw = json.loads(result.stdout)
        
        # Проверяем что есть статус
        assert 'status' in gw, "Отсутствует статус Gateway"
        assert 'conditions' in gw['status'], "Отсутствуют условия Gateway"
        
        # Проверяем что Gateway готов
        ready_condition = None
        for condition in gw['status']['conditions']:
            if condition['type'] == 'Accepted':
                ready_condition = condition
                break
        
        assert ready_condition is not None, "Условие Accepted не найдено"
        assert ready_condition['status'] == 'True', f"Gateway не принят: {ready_condition['message']}"
    
    def test_httproute_status(self):
        """Проверка статуса HTTPRoute"""
        result = subprocess.run([
            'kubectl', 'get', 'httproute', 'ethereum-route', '-n', 'ethereum', '-o', 'json'
        ], capture_output=True, text=True)
        
        assert result.returncode == 0, f"Ошибка получения HTTPRoute: {result.stderr}"
        
        route = json.loads(result.stdout)
        
        # Проверяем что есть статус
        assert 'status' in route, "Отсутствует статус HTTPRoute"
        assert 'parents' in route['status'], "Отсутствуют parents в статусе"
        
        # Проверяем что route привязан к gateway
        assert len(route['status']['parents']) > 0, "Отсутствуют parents"
        
        parent = route['status']['parents'][0]
        assert parent['parentRef']['name'] == 'ethereum-gateway', "Неверный parent gateway"
        
        # Проверяем условия
        assert 'conditions' in parent, "Отсутствуют условия parent"
        
        accepted_condition = None
        for condition in parent['conditions']:
            if condition['type'] == 'Accepted':
                accepted_condition = condition
                break
        
        assert accepted_condition is not None, "Условие Accepted не найдено"
        assert accepted_condition['status'] == 'True', f"HTTPRoute не принят: {accepted_condition['message']}"
    
    def test_secret_exists(self):
        """Проверка что TLS Secret создан"""
        result = subprocess.run([
            'kubectl', 'get', 'secret', 'ethereum-tls-cert', '-n', 'ethereum'
        ], capture_output=True, text=True)
        
        assert result.returncode == 0, "TLS Secret ethereum-tls-cert не найден"
    
    def test_istio_gateway_pods(self):
        """Проверка что поды Istio Gateway запущены"""
        result = subprocess.run([
            'kubectl', 'get', 'pods', '-n', 'istio-system', '-l', 'app=istio-ingressgateway'
        ], capture_output=True, text=True)
        
        assert result.returncode == 0, "Ошибка получения подов Istio Gateway"
        assert 'Running' in result.stdout, "Нет запущенных подов Istio Gateway" 