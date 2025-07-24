#!/bin/bash

# Скрипт для полного развертывания Ethereum Node Infrastructure
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

ENVIRONMENT=${1:-dev}
NAMESPACE=${2:-ethereum}

cd "$REPO_ROOT"

echo "=== Развертывание Ethereum Node Infrastructure ==="
echo "Окружение: $ENVIRONMENT"
echo "Namespace: $NAMESPACE"
echo ""

# Проверяем подключение к кластеру
echo "1. Проверка подключения к кластеру..."
kubectl cluster-info
kubectl get nodes

# Устанавливаем sealed secrets если не установлены
echo ""
echo "2. Проверка sealed secrets..."
if ! kubectl get namespace sealed-secrets &> /dev/null; then
    echo "Установка sealed secrets..."
    bash "$SCRIPT_DIR/install-sealed-secrets.sh"
else
    echo "Sealed secrets уже установлены"
fi

# Устанавливаем cert-manager если не установлен
echo ""
echo "3. Проверка cert-manager..."
if ! kubectl get namespace cert-manager &> /dev/null; then
    echo "Установка cert-manager..."
    kubectl create namespace cert-manager --dry-run=client -o yaml | kubectl apply -f -
    kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml
    echo "Ожидание готовности cert-manager..."
    kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=cert-manager -n cert-manager --timeout=300s
else
    echo "Cert-manager уже установлен"
fi

# Развертываем основную инфраструктуру
echo ""
echo "4. Развертывание основной инфраструктуры..."
echo "Применение инфраструктурной конфигурации..."
kubectl apply -k "$REPO_ROOT/gitops/infrastructure/"

echo "Ожидание готовности базовых компонентов..."
kubectl wait --for=condition=ready pod -l app=ethereum-node -n ethereum --timeout=600s

# Развертываем окружение
echo ""
echo "5. Развертывание окружения: $ENVIRONMENT..."
kubectl apply -k "$REPO_ROOT/gitops/overlays/$ENVIRONMENT/"

echo "Ожидание готовности всех компонентов..."
kubectl wait --for=condition=ready pod -l app=ethereum-node -n ethereum --timeout=600s

# Проверяем статус
echo ""
echo "6. Проверка статуса развертывания..."
echo "Pods:"
kubectl get pods -n ethereum
kubectl get pods -n monitoring

echo ""
echo "Services:"
kubectl get services -n ethereum
kubectl get services -n monitoring

echo ""
echo "=== Развертывание завершено успешно! ==="
echo ""
echo "Доступ к сервисам:"
echo "- Ethereum RPC: kubectl port-forward svc/ethereum-node 8545:8545 -n ethereum"
echo "- Ethereum Metrics: kubectl port-forward svc/ethereum-node 6060:6060 -n ethereum"
echo "- Prometheus: kubectl port-forward svc/prometheus 9090:9090 -n monitoring"
echo "- Grafana: kubectl port-forward svc/grafana 3000:3000 -n monitoring"
echo ""
echo "Логи Ethereum ноды:"
echo "kubectl logs -f statefulset/ethereum-node -n ethereum" 