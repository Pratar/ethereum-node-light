.PHONY: help install check-env test deploy clean dev-setup dev-test build status logs metrics

# Variables
PROJECT_NAME = ethereum-test-node
TERRAFORM_DIR = terraform
ANSIBLE_DIR = ansible
HELM_DIR = helm
TESTS_DIR = tests
SCRIPTS_DIR = scripts

# Colors for output
RED = \033[0;31m
GREEN = \033[0;32m
YELLOW = \033[1;33m
BLUE = \033[0;34m
NC = \033[0m # No Color

help: ## Show help
	@echo "$(BLUE)Available commands:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "$(GREEN)%-20s$(NC) %s\n", $$1, $$2}'

install: ## Install dependencies
	@echo "$(BLUE)Installing dependencies...$(NC)"
	@$(SCRIPTS_DIR)/install-dependencies.sh

check-env: ## Check environment
	@echo "$(BLUE)Checking environment...$(NC)"
	@$(SCRIPTS_DIR)/check-environment.sh

dev-setup: ## Setup local development environment
	@echo "$(BLUE)Setting up local environment...$(NC)"
	@$(SCRIPTS_DIR)/setup-dev-environment.sh

test: ## Run all tests
	@echo "$(BLUE)Running all tests...$(NC)"
	@python3 -m pytest $(TESTS_DIR)/ -v

test-unit: ## Run unit tests
	@echo "$(BLUE)Running unit tests...$(NC)"
	@python3 -m pytest $(TESTS_DIR)/unit/ -v

test-integration: ## Run integration tests
	@echo "$(BLUE)Running integration tests...$(NC)"
	@python3 -m pytest $(TESTS_DIR)/integration/ -v

test-e2e: ## Run E2E tests
	@echo "$(BLUE)Running E2E tests...$(NC)"
	@python3 -m pytest $(TESTS_DIR)/e2e/ -v

dev-test: ## Run tests for local development
	@echo "$(BLUE)Running tests for local development...$(NC)"
	@$(SCRIPTS_DIR)/run-dev-tests.sh

deploy: ## Full deployment
	@echo "$(BLUE)Full deployment...$(NC)"
	@$(SCRIPTS_DIR)/deploy.sh

deploy-infra: ## Deploy infrastructure only
	@echo "$(BLUE)Deploying infrastructure...$(NC)"
	@$(SCRIPTS_DIR)/deploy-infrastructure.sh

deploy-app: ## Deploy application only
	@echo "$(BLUE)Deploying application...$(NC)"
	@$(SCRIPTS_DIR)/deploy-application.sh

build: ## Build images
	@echo "$(BLUE)Building images...$(NC)"
	@$(SCRIPTS_DIR)/build-images.sh

status: ## Show deployment status
	@echo "$(BLUE)Deployment status:$(NC)"
	@$(SCRIPTS_DIR)/show-status.sh

logs: ## Show node logs
	@echo "$(BLUE)Ethereum node logs:$(NC)"
	@$(SCRIPTS_DIR)/show-logs.sh

metrics: ## Show metrics
	@echo "$(BLUE)System metrics:$(NC)"
	@$(SCRIPTS_DIR)/show-metrics.sh

lint: ## Check code with linter
	@echo "$(BLUE)Checking code...$(NC)"
	@$(SCRIPTS_DIR)/lint-code.sh

format: ## Format code
	@echo "$(BLUE)Formatting code...$(NC)"
	@$(SCRIPTS_DIR)/format-code.sh

docs: ## Generate documentation
	@echo "$(BLUE)Generating documentation...$(NC)"
	@$(SCRIPTS_DIR)/generate-docs.sh

clean: ## Clean all resources
	@echo "$(YELLOW)Cleaning resources...$(NC)"
	@$(SCRIPTS_DIR)/cleanup.sh

# Additional development commands
dev-start: ## Start local development environment
	@echo "$(BLUE)Starting local development environment...$(NC)"
	@$(SCRIPTS_DIR)/start-dev-environment.sh

dev-stop: ## Stop local development environment
	@echo "$(BLUE)Stopping local development environment...$(NC)"
	@$(SCRIPTS_DIR)/stop-dev-environment.sh

dev-restart: ## Restart local development environment
	@echo "$(BLUE)Restarting local development environment...$(NC)"
	@make dev-stop
	@make dev-start

# Monitoring commands
monitor: ## Start monitoring
	@echo "$(BLUE)Starting monitoring...$(NC)"
	@$(SCRIPTS_DIR)/start-monitoring.sh

monitor-stop: ## Stop monitoring
	@echo "$(BLUE)Stopping monitoring...$(NC)"
	@$(SCRIPTS_DIR)/stop-monitoring.sh

# Performance testing commands
benchmark: ## Run performance tests
	@echo "$(BLUE)Running performance tests...$(NC)"
	@$(SCRIPTS_DIR)/run-benchmarks.sh

# Security commands
security-scan: ## Security scanning
	@echo "$(BLUE)Running security scan...$(NC)"
	@$(SCRIPTS_DIR)/security-scan.sh

# Backup commands
backup: ## Create backup
	@echo "$(BLUE)Creating backup...$(NC)"
	@$(SCRIPTS_DIR)/backup.sh

restore: ## Restore from backup
	@echo "$(BLUE)Restoring from backup...$(NC)"
	@$(SCRIPTS_DIR)/restore.sh

# Update commands
update: ## Update system
	@echo "$(BLUE)Updating system...$(NC)"
	@$(SCRIPTS_DIR)/update.sh

# Debug commands
debug: ## Enable debug mode
	@echo "$(BLUE)Enabling debug mode...$(NC)"
	@$(SCRIPTS_DIR)/enable-debug.sh

debug-off: ## Disable debug mode
	@echo "$(BLUE)Disabling debug mode...$(NC)"
	@$(SCRIPTS_DIR)/disable-debug.sh 