#!/bin/bash

# Скрипт для установки sealed secrets
set -e

echo "Установка sealed secrets..."

# Создаем namespace
kubectl create namespace sealed-secrets --dry-run=client -o yaml | kubectl apply -f -

# Устанавливаем sealed secrets
helm repo add sealed-secrets https://bitnami-labs.github.io/sealed-secrets
helm repo update

helm install sealed-secrets sealed-secrets/sealed-secrets \
  --namespace sealed-secrets \
  --set fullnameOverride=sealed-secrets

echo "Ожидание готовности sealed secrets..."
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=sealed-secrets -n sealed-secrets --timeout=300s

echo "Получение публичного ключа..."
kubeseal --controller-name=sealed-secrets --controller-namespace=sealed-secrets --fetch-cert > gitops/sealed-secrets-cert.pem

echo "Sealed secrets установлены и настроены!"
echo "Публичный ключ сохранен в: gitops/sealed-secrets-cert.pem" 