# Automatic Scaling for Ethereum Node

## Overview

Stage 4 adds automatic scaling for Ethereum node using HPA (Horizontal Pod Autoscaler) and VPA (Vertical Pod Autoscaler).

## Components

### HPA (Horizontal Pod Autoscaler)
- **Purpose**: Automatic increase/decrease of pod replicas
- **Metrics**: CPU (70%) and Memory (80%)
- **Range**: 1-3 replicas
- **Behavior**: Fast scale up, slow scale down

### VPA (Vertical Pod Autoscaler)
- **Purpose**: Automatic resource adjustment (CPU/Memory)
- **Mode**: Auto (automatic updates)
- **Limits**: 
  - CPU: 100m - 4 cores
  - Memory: 512Mi - 8Gi

### Metrics Server
- **Purpose**: Provide metrics for HPA
- **Version**: v0.6.4
- **Security**: Run as non-privileged user

## Installation

### 1. Metrics Server
```bash
kubectl apply -f k8s/metrics-server.yaml
```

### 2. VPA
```bash
./k8s/install-vpa.sh
```

### 3. HPA and VPA for Ethereum node
```bash
kubectl apply -f k8s/hpa.yaml
kubectl apply -f k8s/vpa.yaml
```

### 4. Scaling alerts
```bash
kubectl apply -f k8s/scaling-alerts.yaml
```

## Monitoring

### Check HPA status
```bash
kubectl get hpa -n ethereum
kubectl describe hpa ethereum-node-hpa -n ethereum
```

### Check VPA status
```bash
kubectl get vpa -n ethereum
kubectl describe vpa ethereum-node-vpa -n ethereum
```

### Check metrics
```bash
kubectl top pods -n ethereum
kubectl top nodes
```

## Configuration

### HPA settings
- **CPU threshold**: 70%
- **Memory threshold**: 80%
- **Scale up**: 100% in 15 seconds
- **Scale down**: 10% in 60 seconds
- **Stabilization window**: 60s (up), 300s (down)

### VPA settings
- **Update mode**: Auto
- **Min CPU**: 100m
- **Max CPU**: 4 cores
- **Min Memory**: 512Mi
- **Max Memory**: 8Gi

## Alerts

1. **EthereumNodeHPAScalingUp** - HPA scaling up
2. **EthereumNodeHPAScalingDown** - HPA scaling down
3. **EthereumNodeVPARecommendation** - VPA recommends changes
4. **EthereumNodeHighCPUUsage** - High CPU usage (>80%)
5. **EthereumNodeHighMemoryUsage** - High Memory usage (>80%)

## Testing

### Load testing
```bash
# Generate CPU load
kubectl run stress-test --image=busybox --rm -it --restart=Never -- sh -c "while true; do echo 'stress test'; done"

# Проверка скалирования
kubectl get hpa -n ethereum -w
```

### Мониторинг VPA
```bash
# Проверка рекомендаций VPA
kubectl describe vpa ethereum-node-vpa -n ethereum
```

## Устранение неполадок

### HPA не работает
1. Проверить metrics-server: `kubectl get pods -n kube-system | grep metrics-server`
2. Проверить API: `kubectl get apiservice v1beta1.metrics.k8s.io`
3. Проверить метрики: `kubectl top pods -n ethereum`

### VPA не работает
1. Проверить VPA поды: `kubectl get pods -n kube-system | grep vpa`
2. Проверить логи: `kubectl logs -n kube-system deployment/vpa-recommender`
3. Проверить CRD: `kubectl get crd | grep vpa`

## Безопасность

- Metrics Server запускается от непривилегированного пользователя
- VPA компоненты имеют минимальные права доступа
- Все компоненты используют SecurityContext
- Алерты настроены для мониторинга аномалий 