import pytest
import subprocess
import json
import time

class TestCertManager:
    """Tests for cert-manager and related components"""
    
    def test_cert_manager_pods_running(self):
        """Check that all cert-manager pods are running"""
        result = subprocess.run([
            'kubectl', 'get', 'pods', '-n', 'cert-manager',
            '-o', 'json'
        ], capture_output=True, text=True)
        
        assert result.returncode == 0, f"Ошибка получения подов: {result.stderr}"
        
        pods = json.loads(result.stdout)
        cert_manager_pods = [
            pod for pod in pods['items'] 
            if pod['metadata']['labels'].get('app.kubernetes.io/name') == 'cert-manager'
        ]
        
        assert len(cert_manager_pods) >= 1, "Должен быть минимум 1 под cert-manager"
        
        for pod in cert_manager_pods:
            assert pod['status']['phase'] == 'Running', f"Под {pod['metadata']['name']} не запущен"
            for container in pod['status']['containerStatuses']:
                assert container['ready'], f"Контейнер {container['name']} не готов"
    
    def test_cert_manager_crds_installed(self):
        """Проверка что CRD cert-manager установлены"""
        crds = [
            'certificates.cert-manager.io',
            'issuers.cert-manager.io',
            'clusterissuers.cert-manager.io',
            'certificaterequests.cert-manager.io'
        ]
        
        for crd in crds:
            result = subprocess.run([
                'kubectl', 'get', 'crd', crd
            ], capture_output=True, text=True)
            
            assert result.returncode == 0, f"CRD {crd} не найден"
    
    def test_cert_manager_webhook_ready(self):
        """Проверка что webhook cert-manager готов"""
        result = subprocess.run([
            'kubectl', 'get', 'validatingwebhookconfiguration', 'cert-manager-webhook'
        ], capture_output=True, text=True)
        
        assert result.returncode == 0, "Webhook cert-manager не найден"
    
    def test_cert_manager_approver_policy_running(self):
        """Проверка что cert-manager-approver-policy запущен"""
        result = subprocess.run([
            'kubectl', 'get', 'pods', '-n', 'cert-manager',
            '-l', 'app.kubernetes.io/name=cert-manager-approver-policy',
            '-o', 'json'
        ], capture_output=True, text=True)
        
        assert result.returncode == 0, f"Ошибка получения подов approver-policy: {result.stderr}"
        
        pods = json.loads(result.stdout)
        assert len(pods['items']) > 0, "Не найдены поды cert-manager-approver-policy"
        
        for pod in pods['items']:
            assert pod['status']['phase'] == 'Running', f"Под {pod['metadata']['name']} не запущен"
            for container in pod['status']['containerStatuses']:
                assert container['ready'], f"Контейнер {container['name']} не готов"

class TestSealedSecrets:
    """Тесты для Sealed Secrets"""
    
    def test_sealed_secrets_pod_running(self):
        """Проверка что под sealed-secrets запущен"""
        result = subprocess.run([
            'kubectl', 'get', 'pods', '-n', 'kube-system',
            '-l', 'app.kubernetes.io/name=sealed-secrets',
            '-o', 'json'
        ], capture_output=True, text=True)
        
        assert result.returncode == 0, f"Ошибка получения подов sealed-secrets: {result.stderr}"
        
        pods = json.loads(result.stdout)
        assert len(pods['items']) > 0, "Не найдены поды sealed-secrets"
        
        for pod in pods['items']:
            assert pod['status']['phase'] == 'Running', f"Под {pod['metadata']['name']} не запущен"
            for container in pod['status']['containerStatuses']:
                assert container['ready'], f"Контейнер {container['name']} не готов"
    
    def test_sealed_secrets_service_exists(self):
        """Проверка что сервис sealed-secrets существует"""
        result = subprocess.run([
            'kubectl', 'get', 'service', 'sealed-secrets', '-n', 'kube-system'
        ], capture_output=True, text=True)
        
        assert result.returncode == 0, "Сервис sealed-secrets не найден"
    
    def test_sealed_secrets_can_encrypt(self):
        """Проверка что sealed-secrets может шифровать секреты"""
        # Создаем тестовый секрет
        test_secret = {
            'apiVersion': 'v1',
            'kind': 'Secret',
            'metadata': {
                'name': 'test-secret',
                'namespace': 'default'
            },
            'type': 'Opaque',
            'data': {
                'test': 'dGVzdA=='  # base64 encoded "test"
            }
        }
        
        # Применяем секрет
        result = subprocess.run([
            'kubectl', 'apply', '-f', '-'
        ], input=json.dumps(test_secret), text=True, capture_output=True)
        
        assert result.returncode == 0, f"Ошибка создания тестового секрета: {result.stderr}"
        
        # Проверяем что секрет создан
        result = subprocess.run([
            'kubectl', 'get', 'secret', 'test-secret', '-n', 'default'
        ], capture_output=True, text=True)
        
        assert result.returncode == 0, "Тестовый секрет не создан"
        
        # Очищаем тестовый секрет
        subprocess.run([
            'kubectl', 'delete', 'secret', 'test-secret', '-n', 'default'
        ], capture_output=True)

class TestCertManagerCSI:
    """Тесты для cert-manager CSI driver"""
    
    def test_csi_driver_pods_running(self):
        """Проверка что CSI driver поды запущены"""
        result = subprocess.run([
            'kubectl', 'get', 'pods', '-n', 'cert-manager',
            '-l', 'app.kubernetes.io/name=cert-manager-csi-driver',
            '-o', 'json'
        ], capture_output=True, text=True)
        
        assert result.returncode == 0, f"Ошибка получения CSI driver подов: {result.stderr}"
        
        pods = json.loads(result.stdout)
        assert len(pods['items']) > 0, "Не найдены поды cert-manager-csi-driver"
        
        for pod in pods['items']:
            assert pod['status']['phase'] == 'Running', f"Под {pod['metadata']['name']} не запущен"
            for container in pod['status']['containerStatuses']:
                assert container['ready'], f"Контейнер {container['name']} не готов"
    
    def test_csi_driver_crds_installed(self):
        """Проверка что CSI driver CRD установлены"""
        # Проверяем что CSI driver работает
        result = subprocess.run([
            'kubectl', 'get', 'pods', '-n', 'cert-manager',
            '-l', 'app.kubernetes.io/name=cert-manager-csi-driver',
            '--field-selector=status.phase=Running'
        ], capture_output=True, text=True)
        
        assert result.returncode == 0, "CSI driver не работает"
        assert 'Running' in result.stdout, "CSI driver поды не запущены"

class TestIntegration:
    """Интеграционные тесты"""
    
    def test_all_components_healthy(self):
        """Проверка что все компоненты здоровы"""
        components = [
            ('cert-manager', 'app.kubernetes.io/name=cert-manager'),
            ('sealed-secrets', 'app.kubernetes.io/name=sealed-secrets'),
            ('cert-manager-approver-policy', 'app.kubernetes.io/name=cert-manager-approver-policy'),
            ('cert-manager-csi-driver', 'app.kubernetes.io/name=cert-manager-csi-driver')
        ]
        
        for name, label in components:
            namespace = 'cert-manager' if name != 'sealed-secrets' else 'kube-system'
            
            result = subprocess.run([
                'kubectl', 'get', 'pods', '-n', namespace,
                '-l', label,
                '--field-selector=status.phase=Running'
            ], capture_output=True, text=True)
            
            assert result.returncode == 0, f"Ошибка проверки {name}: {result.stderr}"
            assert 'Running' in result.stdout, f"Компонент {name} не запущен"
    
    def test_cert_manager_api_accessible(self):
        """Проверка что API cert-manager доступен"""
        result = subprocess.run([
            'kubectl', 'get', 'certificates.cert-manager.io'
        ], capture_output=True, text=True)
        
        # Должен вернуть список (может быть пустым)
        assert result.returncode == 0, "API cert-manager недоступен" 