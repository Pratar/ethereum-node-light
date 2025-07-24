#!/bin/bash

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
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

# Check system requirements
check_system_requirements() {
    log_step "Checking system requirements..."
    
    # Check operating system
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        log_info "✓ Operating system: Linux"
    else
        log_error "✗ Unsupported OS: $OSTYPE"
        exit 1
    fi
    
    # Check architecture
    if [[ $(uname -m) == "x86_64" ]]; then
        log_info "✓ Architecture: x86_64"
    else
        log_error "✗ Unsupported architecture: $(uname -m)"
        exit 1
    fi
    
    # Check free space
    local free_space=$(df . | awk 'NR==2 {print $4}')
    local free_space_gb=$((free_space / 1024 / 1024))
    
    if [[ $free_space_gb -ge 10 ]]; then
        log_info "✓ Free space: ${free_space_gb}GB"
    else
        log_warn "⚠ Low free space: ${free_space_gb}GB (recommended ≥10GB)"
    fi
    
    # Check RAM
    local total_ram=$(free -m | awk 'NR==2{print $2}')
    if [[ $total_ram -ge 4096 ]]; then
        log_info "✓ RAM: ${total_ram}MB"
    else
        log_warn "⚠ Low RAM: ${total_ram}MB (recommended ≥4GB)"
    fi
}

# Check installed tools
check_installed_tools() {
    log_step "Checking installed tools..."
    
    local tools=(
        "terraform:Terraform"
        "ansible:Ansible"
        "docker:Docker"
        "kubectl:kubectl"
        "helm:Helm"
        "python3:Python 3"
        "pip:Python pip"
        "git:Git"
        "curl:cURL"
        "wget:wget"
        "jq:jq"
        "yq:yq"
    )
    
    local missing=()
    local outdated=()
    
    for tool_info in "${tools[@]}"; do
        IFS=':' read -r tool_name tool_display <<< "$tool_info"
        
        if command -v "$tool_name" &> /dev/null; then
            local version=""
            case "$tool_name" in
                "terraform")
                    version=$(terraform --version | head -n1 | cut -d' ' -f2)
                    ;;
                "ansible")
                    version=$(ansible --version | head -n1 | cut -d' ' -f2)
                    ;;
                "docker")
                    version=$(docker --version | cut -d' ' -f3 | sed 's/,//')
                    ;;
                "kubectl")
                    version=$(kubectl version --client --short 2>/dev/null | cut -d' ' -f3)
                    ;;
                "helm")
                    version=$(helm version --short 2>/dev/null | cut -d' ' -f1)
                    ;;
                "python3")
                    version=$(python3 --version 2>&1 | cut -d' ' -f2)
                    ;;
                "pip")
                    version=$(pip --version | cut -d' ' -f2)
                    ;;
                "git")
                    version=$(git --version | cut -d' ' -f3)
                    ;;
                *)
                    version="установлен"
                    ;;
            esac
            log_info "✓ $tool_display: $version"
        else
            missing+=("$tool_display")
            log_error "✗ $tool_display: не установлен"
        fi
    done
    
    if [[ ${#missing[@]} -gt 0 ]]; then
        log_error "Отсутствуют инструменты: ${missing[*]}"
        log_info "Выполните: make install"
        return 1
    fi
}

# Проверка Python окружения
check_python_environment() {
    log_step "Проверка Python окружения..."
    
    if [[ -d "venv" ]]; then
        log_info "✓ Виртуальное окружение найдено"
        
        # Активация виртуального окружения
        source venv/bin/activate
        
        # Проверка установленных пакетов
        local required_packages=(
            "pytest"
            "kubernetes"
            "requests"
            "pyyaml"
            "jinja2"
            "click"
            "rich"
            "web3"
        )
        
        local missing_packages=()
        
        for package in "${required_packages[@]}"; do
            if python -c "import $package" 2>/dev/null; then
                local version=$(pip show $package 2>/dev/null | grep Version | cut -d' ' -f2)
                log_info "✓ $package: $version"
            else
                missing_packages+=("$package")
                log_error "✗ $package: не установлен"
            fi
        done
        
        if [[ ${#missing_packages[@]} -gt 0 ]]; then
            log_error "Отсутствуют Python пакеты: ${missing_packages[*]}"
            log_info "Выполните: pip install ${missing_packages[*]}"
            return 1
        fi
    else
        log_warn "⚠ Виртуальное окружение не найдено"
        log_info "Выполните: python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
        return 1
    fi
}

# Проверка Docker
check_docker() {
    log_step "Проверка Docker..."
    
    if docker info &>/dev/null; then
        log_info "✓ Docker daemon запущен"
        
        # Проверка прав доступа
        if docker ps &>/dev/null; then
            log_info "✓ Права доступа к Docker настроены"
        else
            log_warn "⚠ Нет прав доступа к Docker"
            log_info "Выполните: sudo usermod -aG docker $USER && newgrp docker"
        fi
    else
        log_error "✗ Docker daemon не запущен"
        log_info "Выполните: sudo systemctl start docker"
        return 1
    fi
}

# Проверка Kubernetes
check_kubernetes() {
    log_step "Проверка Kubernetes..."
    
    if kubectl cluster-info &>/dev/null; then
        log_info "✓ Kubernetes кластер доступен"
        
        # Проверка версии
        local k8s_version=$(kubectl version --short 2>/dev/null | grep Server | cut -d' ' -f3)
        log_info "✓ Kubernetes версия: $k8s_version"
    else
        log_warn "⚠ Kubernetes кластер недоступен"
        log_info "Для локальной разработки можно использовать minikube или kind"
    fi
}

# Проверка сетевого доступа
check_network_access() {
    log_step "Проверка сетевого доступа..."
    
    local endpoints=(
        "https://api.github.com:GitHub API"
        "https://registry-1.docker.io:Docker Hub"
        "https://releases.hashicorp.com:HashiCorp"
        "https://dl.k8s.io:Kubernetes"
    )
    
    for endpoint_info in "${endpoints[@]}"; do
        IFS=':' read -r url description <<< "$endpoint_info"
        
        if curl -s --max-time 10 "$url" &>/dev/null; then
            log_info "✓ $description: доступен"
        else
            log_warn "⚠ $description: недоступен"
        fi
    done
}

# Проверка конфигурации проекта
check_project_configuration() {
    log_step "Проверка конфигурации проекта..."
    
    local required_files=(
        "Makefile"
        "README.md"
        ".gitignore"
        "terraform/main.tf"
        "ansible/playbooks/main.yml"
        "helm/ethereum-node/Chart.yaml"
        "tests/unit/"
        "scripts/"
    )
    
    local missing_files=()
    
    for file in "${required_files[@]}"; do
        if [[ -e "$file" ]]; then
            log_info "✓ $file: найден"
        else
            missing_files+=("$file")
            log_error "✗ $file: не найден"
        fi
    done
    
    if [[ ${#missing_files[@]} -gt 0 ]]; then
        log_warn "Отсутствуют файлы: ${missing_files[*]}"
    fi
}

# Проверка прав доступа к файлам
check_file_permissions() {
    log_step "Проверка прав доступа..."
    
    # Проверка исполняемых скриптов
    local scripts_dir="scripts"
    if [[ -d "$scripts_dir" ]]; then
        for script in "$scripts_dir"/*.sh; do
            if [[ -f "$script" ]]; then
                if [[ -x "$script" ]]; then
                    log_info "✓ $script: исполняемый"
                else
                    log_warn "⚠ $script: не исполняемый"
                    chmod +x "$script"
                fi
            fi
        done
    fi
}

# Генерация отчета
generate_report() {
    log_step "Генерация отчета..."
    
    local report_file="environment-check-report.txt"
    
    {
        echo "=== ОТЧЕТ ПРОВЕРКИ ОКРУЖЕНИЯ ==="
        echo "Дата: $(date)"
        echo "Система: $(uname -a)"
        echo ""
        echo "=== СИСТЕМНЫЕ ТРЕБОВАНИЯ ==="
        echo "ОС: $(lsb_release -d 2>/dev/null | cut -f2 || echo "Неизвестно")"
        echo "Архитектура: $(uname -m)"
        echo "RAM: $(free -h | awk 'NR==2{print $2}')"
        echo "Свободное место: $(df -h . | awk 'NR==2{print $4}')"
        echo ""
        echo "=== УСТАНОВЛЕННЫЕ ИНСТРУМЕНТЫ ==="
        echo "Terraform: $(terraform --version 2>/dev/null | head -n1 || echo "Не установлен")"
        echo "Ansible: $(ansible --version 2>/dev/null | head -n1 || echo "Не установлен")"
        echo "Docker: $(docker --version 2>/dev/null || echo "Не установлен")"
        echo "kubectl: $(kubectl version --client --short 2>/dev/null || echo "Не установлен")"
        echo "Helm: $(helm version --short 2>/dev/null || echo "Не установлен")"
        echo "Python: $(python3 --version 2>/dev/null || echo "Не установлен")"
        echo ""
        echo "=== СТАТУС ПРОВЕРКИ ==="
        echo "Все проверки завершены"
    } > "$report_file"
    
    log_info "Отчет сохранен в: $report_file"
}

# Основная функция
main() {
    log_info "Начало проверки окружения для Ethereum Test Node"
    
    local exit_code=0
    
    check_system_requirements || exit_code=1
    check_installed_tools || exit_code=1
    check_python_environment || exit_code=1
    check_docker || exit_code=1
    check_kubernetes || exit_code=1
    check_network_access
    check_project_configuration
    check_file_permissions
    generate_report
    
    if [[ $exit_code -eq 0 ]]; then
        log_info "✓ Проверка окружения завершена успешно!"
        log_info "Окружение готово для разработки"
    else
        log_error "✗ Проверка окружения завершена с ошибками"
        log_info "Исправьте указанные проблемы и повторите проверку"
        exit $exit_code
    fi
}

# Обработка ошибок
trap 'log_error "Ошибка в строке $LINENO. Выход."; exit 1' ERR

# Запуск
main "$@" 