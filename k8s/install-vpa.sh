#!/bin/bash

# Установка VPA (Vertical Pod Autoscaler)
echo "Установка VPA..."

# Клонирование репозитория VPA
git clone https://github.com/kubernetes/autoscaler.git /tmp/autoscaler
cd /tmp/autoscaler/vertical-pod-autoscaler/

# Установка VPA компонентов
kubectl apply -f deploy/vpa-rbac.yaml
kubectl apply -f deploy/admission-controller-deployment.yaml
kubectl apply -f deploy/admission-controller-service.yaml
kubectl apply -f deploy/recommender-deployment.yaml
kubectl apply -f deploy/updater-deployment.yaml
kubectl apply -f deploy/vpa-crd.yaml

# Ожидание готовности подов
echo "Ожидание готовности VPA компонентов..."
kubectl wait --for=condition=ready pod -l app=vpa-admission-controller -n kube-system --timeout=300s
kubectl wait --for=condition=ready pod -l app=vpa-recommender -n kube-system --timeout=300s
kubectl wait --for=condition=ready pod -l app=vpa-updater -n kube-system --timeout=300s

echo "VPA установлен успешно!"
echo "Проверка статуса:"
kubectl get pods -n kube-system | grep vpa 