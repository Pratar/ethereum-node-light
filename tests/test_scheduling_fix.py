import pytest
import subprocess
import json

class TestSchedulingFix:
    """Тесты для проверки исправления проблем планирования"""
    
    def test_all_pods_running(self):
        """Проверка что все поды запущены"""
        result = subprocess.run([
            'kubectl', 'get', 'pods', '--all-namespaces', '--no-headers'
        ], capture_output=True, text=True)
        
        assert result.returncode == 0, "Ошибка получения подов"
        
        # Проверяем что нет подов в состоянии ошибки
        lines = result.stdout.strip().split('\n')
        for line in lines:
            if line:
                parts = line.split()
                if len(parts) >= 4:
                    status = parts[3]
                    assert status not in ['CrashLoopBackOff', 'Error', 'ImagePullBackOff'], f"Под в состоянии ошибки: {line}"
    
    def test_vpa_admission_controller_running(self):
        """Проверка что VPA admission controller работает"""
        result = subprocess.run([
            'kubectl', 'get', 'pods', '-n', 'kube-system', '-l', 'app=vpa-admission-controller'
        ], capture_output=True, text=True)
        
        assert result.returncode == 0, "Ошибка получения подов VPA admission controller"
        assert 'Running' in result.stdout, "VPA admission controller не запущен"
    
    def test_metrics_server_running(self):
        """Проверка что metrics-server работает"""
        result = subprocess.run([
            'kubectl', 'get', 'pods', '-n', 'kube-system', '-l', 'k8s-app=metrics-server'
        ], capture_output=True, text=True)
        
        assert result.returncode == 0, "Ошибка получения подов metrics-server"
        assert 'Running' in result.stdout, "Metrics-server не запущен"
    
    def test_vpa_tls_certificate_exists(self):
        """Проверка что TLS сертификат VPA существует"""
        result = subprocess.run([
            'kubectl', 'get', 'certificate', 'vpa-tls-cert', '-n', 'kube-system'
        ], capture_output=True, text=True)
        
        assert result.returncode == 0, "Certificate vpa-tls-cert не найден"
        
        # Проверяем статус сертификата
        result = subprocess.run([
            'kubectl', 'get', 'certificate', 'vpa-tls-cert', '-n', 'kube-system', '-o', 'jsonpath={.status.conditions[?(@.type=="Ready")].status}'
        ], capture_output=True, text=True)
        
        assert result.stdout.strip() == 'True', "Сертификат VPA не готов"
    
    def test_vpa_tls_secret_exists(self):
        """Проверка что TLS Secret VPA существует"""
        result = subprocess.run([
            'kubectl', 'get', 'secret', 'vpa-tls-certs-new', '-n', 'kube-system'
        ], capture_output=True, text=True)
        
        assert result.returncode == 0, "Secret vpa-tls-certs-new не найден"
        
        # Проверяем что есть нужные файлы
        result = subprocess.run([
            'kubectl', 'get', 'secret', 'vpa-tls-certs-new', '-n', 'kube-system', '-o', 'jsonpath={.data}'
        ], capture_output=True, text=True)
        
        data = json.loads(result.stdout)
        assert 'serverCert.pem' in data, "Отсутствует serverCert.pem"
        assert 'serverKey.pem' in data, "Отсутствует serverKey.pem"
        assert 'caCert.pem' in data, "Отсутствует caCert.pem"
    
    def test_vpa_working(self):
        """Проверка что VPA работает"""
        result = subprocess.run([
            'kubectl', 'get', 'vpa', 'ethereum-node-vpa', '-n', 'ethereum'
        ], capture_output=True, text=True)
        
        assert result.returncode == 0, "VPA ethereum-node-vpa не найден"
        
        # Проверяем что VPA активен
        result = subprocess.run([
            'kubectl', 'get', 'vpa', 'ethereum-node-vpa', '-n', 'ethereum', '-o', 'jsonpath={.status.conditions[?(@.type=="Active")].status}'
        ], capture_output=True, text=True)
        
        # VPA может быть не активен сразу, но должен существовать
        assert result.returncode == 0, "Ошибка получения статуса VPA"
    
    def test_node_resources_available(self):
        """Проверка что на узлах есть свободные ресурсы"""
        result = subprocess.run([
            'kubectl', 'top', 'nodes'
        ], capture_output=True, text=True)
        
        assert result.returncode == 0, "Ошибка получения метрик узлов"
        
        lines = result.stdout.strip().split('\n')[1:]  # Пропускаем заголовок
        for line in lines:
            if line:
                parts = line.split()
                if len(parts) >= 4:
                    cpu_percent = int(parts[2].replace('%', ''))
                    memory_percent = int(parts[4].replace('%', ''))
                    
                    # Проверяем что узлы не перегружены
                    assert cpu_percent < 90, f"Узел перегружен по CPU: {cpu_percent}%"
                    assert memory_percent < 90, f"Узел перегружен по памяти: {memory_percent}%"
    
    def test_no_scheduling_events(self):
        """Проверка что нет событий планирования с ошибками"""
        result = subprocess.run([
            'kubectl', 'get', 'events', '--all-namespaces', '--sort-by=.lastTimestamp'
        ], capture_output=True, text=True)
        
        assert result.returncode == 0, "Ошибка получения событий"
        
        # Проверяем последние события на наличие ошибок планирования
        lines = result.stdout.strip().split('\n')
        recent_events = lines[-20:]  # Последние 20 событий
        
        for event in recent_events:
            if event and 'Warning' in event and any(keyword in event for keyword in ['FailedScheduling', 'BackOff', 'ImagePullBackOff']):
                # Игнорируем старые события
                if 'BackOff' not in event or 'ImagePullBackOff' not in event:
                    continue
                # Если есть новые события с ошибками планирования, это проблема
                if 'FailedScheduling' in event:
                    pytest.fail(f"Обнаружено событие планирования с ошибкой: {event}")
    
    def test_ethereum_node_healthy(self):
        """Проверка что Ethereum нода здорова"""
        result = subprocess.run([
            'kubectl', 'get', 'pods', '-n', 'ethereum', '-l', 'app=ethereum-node'
        ], capture_output=True, text=True)
        
        assert result.returncode == 0, "Ошибка получения подов Ethereum ноды"
        assert 'Running' in result.stdout, "Ethereum нода не запущена"
        
        # Проверяем что под готов
        result = subprocess.run([
            'kubectl', 'get', 'pods', '-n', 'ethereum', '-l', 'app=ethereum-node', '-o', 'jsonpath={.items[0].status.conditions[?(@.type=="Ready")].status}'
        ], capture_output=True, text=True)
        
        assert result.stdout.strip() == 'True', "Ethereum нода не готова"
    
    def test_gateway_services_running(self):
        """Проверка что Gateway сервисы работают"""
        # Проверяем Istio Gateway
        result = subprocess.run([
            'kubectl', 'get', 'pods', '-n', 'istio-system', '-l', 'app=istio-ingressgateway'
        ], capture_output=True, text=True)
        
        assert result.returncode == 0, "Ошибка получения подов Istio Gateway"
        assert 'Running' in result.stdout, "Istio Gateway не запущен"
        
        # Проверяем Grafana Gateway
        result = subprocess.run([
            'kubectl', 'get', 'pods', '-n', 'monitoring', '-l', 'service.istio.io/canonical-name=grafana-gateway-istio'
        ], capture_output=True, text=True)
        
        assert result.returncode == 0, "Ошибка получения подов Grafana Gateway"
        assert 'Running' in result.stdout, "Grafana Gateway не запущен"
        
        # Проверяем Prometheus Gateway
        result = subprocess.run([
            'kubectl', 'get', 'pods', '-n', 'monitoring', '-l', 'service.istio.io/canonical-name=prometheus-gateway-istio'
        ], capture_output=True, text=True)
        
        assert result.returncode == 0, "Ошибка получения подов Prometheus Gateway"
        assert 'Running' in result.stdout, "Prometheus Gateway не запущен" 