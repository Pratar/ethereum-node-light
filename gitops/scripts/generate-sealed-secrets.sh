#!/bin/bash

# Скрипт для генерации sealed secrets
# Использование: ./generate-sealed-secrets.sh [namespace]

set -e

NAMESPACE=${1:-ethereum}
CLUSTER_NAME=${2:-ethereum-cluster}

echo "Генерация sealed secrets для namespace: $NAMESPACE"

# Проверяем, что kubeseal установлен
if ! command -v kubeseal &> /dev/null; then
    echo "Ошибка: kubeseal не установлен"
    echo "Установите: brew install kubeseal (macOS) или скачайте с GitHub"
    exit 1
fi

# Создаем временные секреты
cat <<EOF > /tmp/ethereum-secrets.yaml
apiVersion: v1
kind: Secret
metadata:
  name: ethereum-node-secrets
  namespace: $NAMESPACE
type: Opaque
data:
  ethereum-rpc-password: $(echo -n "secure-rpc-password" | base64)
  ethereum-p2p-key: $(echo -n "secure-p2p-key" | base64)
  prometheus-basic-auth: $(echo -n "admin:secure-password" | base64)
EOF

cat <<EOF > /tmp/prometheus-secrets.yaml
apiVersion: v1
kind: Secret
metadata:
  name: prometheus-secrets
  namespace: monitoring
type: Opaque
data:
  prometheus-admin-password: $(echo -n "secure-prometheus-password" | base64)
  grafana-admin-password: $(echo -n "secure-grafana-password" | base64)
EOF

# Генерируем sealed secrets
echo "Генерация sealed secret для Ethereum..."
kubeseal --format=yaml < /tmp/ethereum-secrets.yaml > gitops/base/secrets/ethereum-sealed-secret.yaml

echo "Генерация sealed secret для Prometheus..."
kubeseal --format=yaml < /tmp/prometheus-secrets.yaml > gitops/base/secrets/prometheus-sealed-secret.yaml

# Очищаем временные файлы
rm /tmp/ethereum-secrets.yaml
rm /tmp/prometheus-secrets.yaml

echo "Sealed secrets созданы:"
echo "- gitops/base/secrets/ethereum-sealed-secret.yaml"
echo "- gitops/base/secrets/prometheus-sealed-secret.yaml"

echo ""
echo "ВАЖНО: Сохраните публичный ключ sealed secrets:"
echo "kubeseal --fetch-cert > gitops/sealed-secrets-cert.pem" 