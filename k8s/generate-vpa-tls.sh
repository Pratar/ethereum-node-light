#!/bin/bash

# Генерация TLS сертификатов для VPA
echo "Генерация TLS сертификатов для VPA..."

# Создание временной директории
TEMP_DIR=$(mktemp -d)
cd $TEMP_DIR

# Генерация приватного ключа
openssl genrsa -out ca.key 2048

# Генерация CA сертификата
openssl req -new -x509 -key ca.key -sha256 -subj "/C=US/ST=CA/L=San Francisco/O=VPA/CN=VPA CA" -days 3650 -out ca.crt

# Генерация приватного ключа для сервера
openssl genrsa -out server.key 2048

# Создание конфигурации для CSR
cat > server.conf << EOF
[req]
req_extensions = v3_req
distinguished_name = req_distinguished_name
[req_distinguished_name]
C = US
ST = CA
L = San Francisco
O = VPA
CN = vpa-admission-controller.kube-system.svc
[v3_req]
basicConstraints = CA:FALSE
keyUsage = nonRepudiation, digitalSignature, keyEncipherment
extendedKeyUsage = serverAuth
subjectAltName = @alt_names
[alt_names]
DNS.1 = vpa-admission-controller.kube-system.svc
DNS.2 = vpa-admission-controller.kube-system.svc.cluster.local
DNS.3 = vpa-webhook.kube-system.svc
DNS.4 = vpa-webhook.kube-system.svc.cluster.local
EOF

# Генерация CSR
openssl req -new -key server.key -out server.csr -config server.conf -subj "/C=US/ST=CA/L=San Francisco/O=VPA/CN=vpa-admission-controller.kube-system.svc"

# Подписание сертификата
openssl x509 -req -in server.csr -CA ca.crt -CAkey ca.key -CAcreateserial -out server.crt -days 365 -extensions v3_req -extfile server.conf

# Создание секрета в Kubernetes
kubectl create secret tls vpa-tls-certs \
  --cert=server.crt \
  --key=server.key \
  --namespace=kube-system

# Создание ConfigMap с CA сертификатом
kubectl create configmap vpa-ca-certs \
  --from-file=ca.crt \
  --namespace=kube-system

# Очистка временной директории
cd -
rm -rf $TEMP_DIR

echo "TLS сертификаты для VPA созданы успешно!"
echo "Проверка секрета:"
kubectl get secret vpa-tls-certs -n kube-system 