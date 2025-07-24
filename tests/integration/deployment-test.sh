#!/bin/bash

# Интеграционные тесты для Ethereum ноды
set -e

echo "=== Интеграционные тесты Ethereum ноды ==="

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Функции для тестирования
test_cluster_connectivity() {
    echo -e "${YELLOW}Тест 1: Подключение к кластеру${NC}"
    
    if kubectl cluster-info > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Кластер доступен${NC}"
        return 0
    else
        echo -e "${RED}✗ Кластер недоступен${NC}"
        return 1
    fi
}

test_namespace_exists() {
    echo -e "${YELLOW}Тест 2: Проверка namespace${NC}"
    
    if kubectl get namespace ethereum > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Namespace ethereum существует${NC}"
        return 0
    else
        echo -e "${RED}✗ Namespace ethereum не существует${NC}"
        return 1
    fi
}

test_ethereum_pod_running() {
    echo -e "${YELLOW}Тест 3: Проверка работы Ethereum ноды${NC}"
    
    # Ждем пока под запустится
    echo "Ожидание запуска Ethereum ноды..."
    kubectl wait --for=condition=ready pod -l app=ethereum-node -n ethereum --timeout=600s
    
    if kubectl get pods -n ethereum -l app=ethereum-node | grep -q "Running"; then
        echo -e "${GREEN}✓ Ethereum нода запущена${NC}"
        return 0
    else
        echo -e "${RED}✗ Ethereum нода не запущена${NC}"
        return 1
    fi
}

test_service_connectivity() {
    echo -e "${YELLOW}Тест 4: Проверка доступности сервиса${NC}"
    
    # Port forward для тестирования
    kubectl port-forward service/ethereum-node-service 8545:8545 -n ethereum &
    PF_PID=$!
    
    # Ждем пока port-forward запустится
    sleep 5
    
    # Тест RPC API
    response=$(curl -s -X POST -H "Content-Type: application/json" \
        --data '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}' \
        http://localhost:8545)
    
    if echo "$response" | grep -q "result"; then
        echo -e "${GREEN}✓ RPC API доступен${NC}"
        result=0
    else
        echo -e "${RED}✗ RPC API недоступен${NC}"
        result=1
    fi
    
    # Останавливаем port-forward
    kill $PF_PID 2>/dev/null || true
    
    return $result
}

test_monitoring() {
    echo -e "${YELLOW}Тест 5: Проверка мониторинга${NC}"
    
    # Проверяем что Prometheus работает
    if kubectl get pods -n monitoring | grep -q "prometheus.*Running"; then
        echo -e "${GREEN}✓ Prometheus запущен${NC}"
        return 0
    else
        echo -e "${RED}✗ Prometheus не запущен${NC}"
        return 1
    fi
}

test_security() {
    echo -e "${YELLOW}Тест 6: Проверка безопасности${NC}"
    
    # Проверяем Network Policies
    if kubectl get networkpolicy -n ethereum > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Network Policies настроены${NC}"
        return 0
    else
        echo -e "${RED}✗ Network Policies не настроены${NC}"
        return 1
    fi
}

test_storage() {
    echo -e "${YELLOW}Тест 7: Проверка хранилища${NC}"
    
    # Проверяем PVC
    if kubectl get pvc -n ethereum | grep -q "ethereum-data-pvc.*Bound"; then
        echo -e "${GREEN}✓ Persistent Volume Claim привязан${NC}"
        return 0
    else
        echo -e "${RED}✗ Persistent Volume Claim не привязан${NC}"
        return 1
    fi
}

# Основная функция тестирования
run_tests() {
    local failed_tests=0
    local total_tests=7
    
    echo "Запуск интеграционных тестов..."
    echo "=================================="
    
    # Запуск всех тестов
    test_cluster_connectivity || ((failed_tests++))
    test_namespace_exists || ((failed_tests++))
    test_ethereum_pod_running || ((failed_tests++))
    test_service_connectivity || ((failed_tests++))
    test_monitoring || ((failed_tests++))
    test_security || ((failed_tests++))
    test_storage || ((failed_tests++))
    
    echo "=================================="
    echo "Результаты тестирования:"
    echo "Пройдено: $((total_tests - failed_tests))/$total_tests"
    
    if [ $failed_tests -eq 0 ]; then
        echo -e "${GREEN}Все тесты пройдены успешно!${NC}"
        exit 0
    else
        echo -e "${RED}Провалено тестов: $failed_tests${NC}"
        exit 1
    fi
}

# Проверка зависимостей
check_dependencies() {
    echo "Проверка зависимостей..."
    
    if ! command -v kubectl &> /dev/null; then
        echo -e "${RED}Ошибка: kubectl не установлен${NC}"
        exit 1
    fi
    
    if ! command -v curl &> /dev/null; then
        echo -e "${RED}Ошибка: curl не установлен${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}Все зависимости установлены${NC}"
}

# Главная функция
main() {
    check_dependencies
    run_tests
}

# Запуск скрипта
main "$@" 