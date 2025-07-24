#!/bin/bash

# Скрипт для развертывания на новом кластере
set -e

ENVIRONMENT=${1:-dev}

echo "=== Развертывание Ethereum Node Infrastructure на новом кластере ==="
echo "Окружение: $ENVIRONMENT"
echo ""

# Проверяем подключение к кластеру
echo "1. Проверка подключения к кластеру..."
kubectl cluster-info
kubectl get nodes

# Устанавливаем sealed secrets
echo ""
echo "2. Установка sealed secrets..."
kubectl create namespace sealed-secrets --dry-run=client -o yaml | kubectl apply -f -

helm repo add sealed-secrets https://bitnami-labs.github.io/sealed-secrets
helm repo update

helm install sealed-secrets sealed-secrets/sealed-secrets \
  --namespace sealed-secrets \
  --set fullnameOverride=sealed-secrets

echo "Ожидание готовности sealed secrets..."
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=sealed-secrets -n sealed-secrets --timeout=300s

echo "Получение публичного ключа..."
kubeseal --fetch-cert > gitops/sealed-secrets-cert.pem

# Устанавливаем cert-manager
echo ""
echo "3. Установка cert-manager..."
kubectl create namespace cert-manager --dry-run=client -o yaml | kubectl apply -f -
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml
echo "Ожидание готовности cert-manager..."
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=cert-manager -n cert-manager --timeout=300s

# Развертываем основную инфраструктуру
echo ""
echo "4. Развертывание основной инфраструктуры..."
echo "Применение базовой конфигурации..."
kubectl apply -k gitops/base/

echo "Ожидание готовности базовых компонентов..."
kubectl wait --for=condition=ready pod -l app=ethereum-node -n ethereum --timeout=600s

# Развертываем окружение
echo ""
echo "5. Развертывание окружения: $ENVIRONMENT..."
kubectl apply -k gitops/overlays/$ENVIRONMENT/

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