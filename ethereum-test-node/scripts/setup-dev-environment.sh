#!/bin/bash

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функции логирования
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# Создание виртуального окружения Python
setup_python_environment() {
    log_step "Настройка Python окружения..."
    
    if [[ ! -d "venv" ]]; then
        log_info "Создание виртуального окружения..."
        python3 -m venv venv
    fi
    
    # Активация виртуального окружения
    source venv/bin/activate
    
    # Обновление pip
    pip install --upgrade pip
    
    # Создание requirements.txt если не существует
    if [[ ! -f "requirements.txt" ]]; then
        log_info "Создание requirements.txt..."
        cat > requirements.txt << EOF
# Testing
pytest>=7.0.0
pytest-cov>=4.0.0
pytest-mock>=3.10.0
pytest-asyncio>=0.21.0

# Kubernetes
kubernetes>=28.0.0

# HTTP requests
requests>=2.31.0

# YAML processing
pyyaml>=6.0.1

# Template engine
jinja2>=3.1.2

# CLI framework
click>=8.1.0

# Rich terminal output
rich>=13.0.0
tabulate>=0.9.0

# Monitoring
prometheus-client>=0.17.0

# Ethereum
web3>=6.0.0
eth-account>=0.9.0
eth-utils>=2.0.0

# Development tools
black>=23.0.0
flake8>=6.0.0
mypy>=1.0.0
pre-commit>=3.0.0
EOF
    fi
    
    # Установка зависимостей
    log_info "Установка Python зависимостей..."
    pip install -r requirements.txt
    
    log_info "Python окружение настроено"
}

# Настройка pre-commit hooks
setup_pre_commit() {
    log_step "Настройка pre-commit hooks..."
    
    if command -v pre-commit &> /dev/null; then
        # Создание .pre-commit-config.yaml
        if [[ ! -f ".pre-commit-config.yaml" ]]; then
            log_info "Создание конфигурации pre-commit..."
            cat > .pre-commit-config.yaml << EOF
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
      - id: check-merge-conflict
      - id: debug-statements

  - repo: https://github.com/psf/black
    rev: 23.3.0
    hooks:
      - id: black
        language_version: python3

  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
        args: [--max-line-length=88, --extend-ignore=E203,W503]

  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort
        args: [--profile=black]

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.3.0
    hooks:
      - id: mypy
        additional_dependencies: [types-requests, types-PyYAML]
EOF
        fi
        
        # Установка pre-commit hooks
        pre-commit install
        
        log_info "Pre-commit hooks настроены"
    else
        log_warn "Pre-commit не установлен, пропускаем настройку hooks"
    fi
}

# Настройка локального Kubernetes кластера
setup_local_kubernetes() {
    log_step "Настройка локального Kubernetes кластера..."
    
    # Проверка доступности kubectl
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl не установлен"
        return 1
    fi
    
    # Попытка подключения к существующему кластеру
    if kubectl cluster-info &>/dev/null; then
        log_info "Kubernetes кластер уже доступен"
        return 0
    fi
    
    # Установка minikube если доступен
    if command -v minikube &> /dev/null; then
        log_info "Запуск minikube..."
        minikube start --driver=docker --memory=4096 --cpus=2
        minikube addons enable ingress
        minikube addons enable metrics-server
        
        log_info "Minikube запущен"
        return 0
    fi
    
    # Установка kind если доступен
    if command -v kind &> /dev/null; then
        log_info "Создание кластера kind..."
        kind create cluster --name ethereum-test --config - << EOF
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
- role: control-plane
  extraPortMappings:
  - containerPort: 80
    hostPort: 80
  - containerPort: 443
    hostPort: 443
- role: worker
- role: worker
EOF
        log_info "Kind кластер создан"
        return 0
    fi
    
    log_warn "Не найден локальный Kubernetes кластер"
    log_info "Установите minikube или kind для локальной разработки"
    return 1
}

# Настройка локального Docker registry
setup_docker_registry() {
    log_step "Настройка локального Docker registry..."
    
    # Проверка доступности Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker не установлен"
        return 1
    fi
    
    # Запуск локального registry
    if ! docker ps | grep -q "registry:2"; then
        log_info "Запуск локального Docker registry..."
        docker run -d \
            --name local-registry \
            --restart=always \
            -p 5000:5000 \
            -v registry-data:/var/lib/registry \
            registry:2
        
        log_info "Локальный Docker registry запущен на порту 5000"
    else
        log_info "Локальный Docker registry уже запущен"
    fi
}

# Создание конфигурационных файлов
create_config_files() {
    log_step "Создание конфигурационных файлов..."
    
    # Создание .env файла
    if [[ ! -f ".env" ]]; then
        log_info "Создание .env файла..."
        cat > .env << EOF
# Ethereum Node Configuration
ETHEREUM_NETWORK=testnet
ETHEREUM_SYNC_MODE=light
ETHEREUM_MAX_PEERS=10
ETHEREUM_BLOCK_LIMIT=100
ETHEREUM_HTTP_PORT=8545
ETHEREUM_P2P_PORT=30303

# Docker Configuration
DOCKER_REGISTRY=localhost:5000
DOCKER_IMAGE_NAME=ethereum-test-node
DOCKER_IMAGE_TAG=latest

# Kubernetes Configuration
K8S_NAMESPACE=ethereum-test
K8S_STORAGE_CLASS=local-storage

# Monitoring Configuration
PROMETHEUS_PORT=9090
GRAFANA_PORT=3000

# Development Configuration
DEBUG=true
LOG_LEVEL=INFO
EOF
    fi
    
    # Создание docker-compose.yml для локальной разработки
    if [[ ! -f "docker-compose.yml" ]]; then
        log_info "Создание docker-compose.yml..."
        cat > docker-compose.yml << EOF
version: '3.8'

services:
  ethereum-node:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: ethereum-test-node
    ports:
      - "8545:8545"
      - "30303:30303"
    environment:
      - ETHEREUM_NETWORK=testnet
      - ETHEREUM_SYNC_MODE=light
      - ETHEREUM_BLOCK_LIMIT=100
    volumes:
      - ethereum-data:/data
    restart: unless-stopped
    networks:
      - ethereum-network

  prometheus:
    image: prom/prometheus:latest
    container_name: prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus-data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
      - '--storage.tsdb.retention.time=200h'
      - '--web.enable-lifecycle'
    restart: unless-stopped
    networks:
      - ethereum-network

  grafana:
    image: grafana/grafana:latest
    container_name: grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana-data:/var/lib/grafana
      - ./monitoring/grafana/dashboards:/etc/grafana/provisioning/dashboards
      - ./monitoring/grafana/datasources:/etc/grafana/provisioning/datasources
    restart: unless-stopped
    networks:
      - ethereum-network

volumes:
  ethereum-data:
  prometheus-data:
  grafana-data:

networks:
  ethereum-network:
    driver: bridge
EOF
    fi
    
    # Создание директорий для мониторинга
    mkdir -p monitoring/{prometheus,grafana/{dashboards,datasources}}
    
    # Создание конфигурации Prometheus
    if [[ ! -f "monitoring/prometheus.yml" ]]; then
        log_info "Создание конфигурации Prometheus..."
        cat > monitoring/prometheus.yml << EOF
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  # - "first_rules.yml"
  # - "second_rules.yml"

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  - job_name: 'ethereum-node'
    static_configs:
      - targets: ['ethereum-node:8545']
    metrics_path: /metrics
    scrape_interval: 30s
EOF
    fi
    
    log_info "Конфигурационные файлы созданы"
}

# Настройка IDE конфигурации
setup_ide_config() {
    log_step "Настройка IDE конфигурации..."
    
    # Создание .vscode директории и настроек
    mkdir -p .vscode
    
    if [[ ! -f ".vscode/settings.json" ]]; then
        log_info "Создание настроек VS Code..."
        cat > .vscode/settings.json << EOF
{
    "python.defaultInterpreterPath": "./venv/bin/python",
    "python.linting.enabled": true,
    "python.linting.flake8Enabled": true,
    "python.formatting.provider": "black",
    "python.formatting.blackArgs": ["--line-length=88"],
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
        "source.organizeImports": true
    },
    "files.exclude": {
        "**/__pycache__": true,
        "**/*.pyc": true,
        "venv": true,
        ".pytest_cache": true
    },
    "terraform.languageServer.enable": true,
    "yaml.schemas": {
        "https://json.schemastore.org/github-workflow.json": ".github/workflows/*.yml"
    }
}
EOF
    fi
    
    if [[ ! -f ".vscode/launch.json" ]]; then
        log_info "Создание конфигурации отладки..."
        cat > .vscode/launch.json << EOF
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Python: Current File",
            "type": "python",
            "request": "launch",
            "program": "\${file}",
            "console": "integratedTerminal",
            "cwd": "\${workspaceFolder}",
            "python": "\${workspaceFolder}/venv/bin/python"
        },
        {
            "name": "Python: Tests",
            "type": "python",
            "request": "launch",
            "module": "pytest",
            "args": ["-v"],
            "console": "integratedTerminal",
            "cwd": "\${workspaceFolder}",
            "python": "\${workspaceFolder}/venv/bin/python"
        }
    ]
}
EOF
    fi
    
    log_info "IDE конфигурация настроена"
}

# Создание базовых тестов
create_basic_tests() {
    log_step "Создание базовых тестов..."
    
    # Создание __init__.py файлов
    touch src/__init__.py
    touch src/ethereum/__init__.py
    touch src/monitoring/__init__.py
    touch tests/__init__.py
    touch tests/unit/__init__.py
    touch tests/integration/__init__.py
    touch tests/e2e/__init__.py
    
    # Создание базового теста
    if [[ ! -f "tests/unit/test_basic.py" ]]; then
        log_info "Создание базового unit теста..."
        cat > tests/unit/test_basic.py << EOF
import pytest
import sys
import os

# Добавление src в путь
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))

def test_import_ethereum():
    """Тест импорта модуля ethereum"""
    try:
        import ethereum
        assert True
    except ImportError:
        pytest.fail("Не удалось импортировать модуль ethereum")

def test_import_monitoring():
    """Тест импорта модуля monitoring"""
    try:
        import monitoring
        assert True
    except ImportError:
        pytest.fail("Не удалось импортировать модуль monitoring")

def test_basic_math():
    """Простой тест математики"""
    assert 2 + 2 == 4
    assert 10 - 5 == 5
    assert 3 * 4 == 12
    assert 15 / 3 == 5

def test_string_operations():
    """Тест строковых операций"""
    test_string = "Ethereum Test Node"
    assert len(test_string) == 17
    assert "Ethereum" in test_string
    assert test_string.upper() == "ETHEREUM TEST NODE"
EOF
    fi
    
    log_info "Базовые тесты созданы"
}

# Основная функция
main() {
    log_info "Настройка локального окружения разработки для Ethereum Test Node"
    
    setup_python_environment
    setup_pre_commit
    setup_local_kubernetes
    setup_docker_registry
    create_config_files
    setup_ide_config
    create_basic_tests
    
    log_info "✓ Локальное окружение разработки настроено успешно!"
    log_info ""
    log_info "Следующие шаги:"
    log_info "1. Активируйте виртуальное окружение: source venv/bin/activate"
    log_info "2. Запустите тесты: make test"
    log_info "3. Запустите локальную разработку: make dev-start"
    log_info ""
    log_info "Доступные команды:"
    log_info "- make test: запуск всех тестов"
    log_info "- make dev-start: запуск локальной среды"
    log_info "- make dev-stop: остановка локальной среды"
    log_info "- make status: проверка статуса"
}

# Обработка ошибок
trap 'log_error "Ошибка в строке $LINENO. Выход."; exit 1' ERR

# Запуск
main "$@" 