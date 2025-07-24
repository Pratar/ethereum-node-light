"""
Ethereum Node

Main module for working with Ethereum test node.
"""

import os
import time
import logging
import subprocess
import threading
from typing import Optional, Dict, Any, List
from dataclasses import dataclass

from .config import EthereumConfig
from .storage import BlockStorage

logger = logging.getLogger(__name__)


@dataclass
class NodeStatus:
    """Node status"""
    is_running: bool = False
    is_syncing: bool = False
    current_block: Optional[int] = None
    peer_count: int = 0
    uptime_seconds: int = 0
    last_error: Optional[str] = None


class EthereumNode:
    """Ethereum node with block limit"""
    
    def __init__(self, config: EthereumConfig, data_dir: str = "/data"):
        """
        Initialize Ethereum node
        
        Args:
            config: Node configuration
            data_dir: Data directory
        """
        self.config = config
        self.data_dir = data_dir
        self.storage = BlockStorage(data_dir, config.block_limit)
        
        # Geth process
        self.geth_process: Optional[subprocess.Popen] = None
        self.status = NodeStatus()
        
        # Monitoring thread
        self.monitor_thread: Optional[threading.Thread] = None
        self.shutdown_event = threading.Event()
        
        # Create directories
        self._ensure_directories()
        
        logger.info(f"Ethereum node initialized: {config}")
    
    def _ensure_directories(self):
        """Create necessary directories"""
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.config.data_dir, exist_ok=True)
        os.makedirs(self.config.config_dir, exist_ok=True)
    
    def start(self) -> bool:
        """
        Start node
        
        Returns:
            True if node started successfully
        """
        if self.is_running():
            logger.warning("Node is already running")
            return True
        
        try:
            # Prepare command line arguments
            geth_args = self.config.get_geth_args()
            
            # Start Geth process
            self.geth_process = subprocess.Popen(
                ["geth"] + geth_args,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            # Update status
            self.status.is_running = True
            self.status.uptime_seconds = 0
            
            # Start monitoring
            self._start_monitoring()
            
            logger.info("Ethereum node started")
            return True
            
        except Exception as e:
            error_msg = f"Ошибка запуска ноды: {e}"
            logger.error(error_msg)
            self.status.last_error = error_msg
            return False
    
    def stop(self) -> bool:
        """
        Остановка ноды
        
        Returns:
            True если нода остановлена успешно
        """
        if not self.is_running():
            logger.warning("Нода не запущена")
            return True
        
        try:
            # Остановка мониторинга
            self._stop_monitoring()
            
            # Остановка процесса Geth
            if self.geth_process:
                self.geth_process.terminate()
                
                # Ожидание завершения
                try:
                    self.geth_process.wait(timeout=30)
                except subprocess.TimeoutExpired:
                    logger.warning("Принудительное завершение процесса Geth")
                    self.geth_process.kill()
                    self.geth_process.wait()
                
                self.geth_process = None
            
            # Обновление статуса
            self.status.is_running = False
            self.status.is_syncing = False
            
            logger.info("Ethereum нода остановлена")
            return True
            
        except Exception as e:
            error_msg = f"Ошибка остановки ноды: {e}"
            logger.error(error_msg)
            self.status.last_error = error_msg
            return False
    
    def restart(self) -> bool:
        """
        Перезапуск ноды
        
        Returns:
            True если перезапуск выполнен успешно
        """
        logger.info("Перезапуск Ethereum ноды")
        
        if not self.stop():
            return False
        
        # Небольшая пауза перед запуском
        time.sleep(2)
        
        return self.start()
    
    def is_running(self) -> bool:
        """
        Проверка, запущена ли нода
        
        Returns:
            True если нода запущена
        """
        if self.geth_process is None:
            return False
        
        # Проверка, что процесс все еще работает
        return self.geth_process.poll() is None
    
    def get_status(self) -> NodeStatus:
        """
        Получение статуса ноды
        
        Returns:
            Статус ноды
        """
        # Обновление статуса запуска
        self.status.is_running = self.is_running()
        
        # Обновление времени работы
        if self.status.is_running and self.geth_process:
            self.status.uptime_seconds = int(time.time() - self.geth_process.start_time)
        
        return self.status
    
    def get_logs(self, lines: int = 100) -> List[str]:
        """
        Получение логов ноды
        
        Args:
            lines: Количество последних строк
            
        Returns:
            Список строк логов
        """
        if not self.is_running():
            return []
        
        try:
            # Чтение логов из файла (если настроено логирование в файл)
            log_file = os.path.join(self.data_dir, "geth.log")
            if os.path.exists(log_file):
                with open(log_file, 'r') as f:
                    all_lines = f.readlines()
                    return all_lines[-lines:] if len(all_lines) > lines else all_lines
            
            return []
            
        except Exception as e:
            logger.error(f"Ошибка чтения логов: {e}")
            return []
    
    def add_block(self, block_number: int, block_data: Dict[str, Any]) -> bool:
        """
        Добавление блока в хранилище
        
        Args:
            block_number: Номер блока
            block_data: Данные блока
            
        Returns:
            True если блок добавлен
        """
        return self.storage.add_block(block_number, block_data)
    
    def get_block(self, block_number: int) -> Optional[Dict[str, Any]]:
        """
        Получение блока
        
        Args:
            block_number: Номер блока
            
        Returns:
            Данные блока или None
        """
        return self.storage.get_block(block_number)
    
    def get_storage_statistics(self) -> Dict[str, Any]:
        """
        Получение статистики хранилища
        
        Returns:
            Статистика хранилища
        """
        return self.storage.get_statistics()
    
    def cleanup_old_blocks(self, keep_blocks: int = None):
        """
        Очистка старых блоков
        
        Args:
            keep_blocks: Количество блоков для сохранения
        """
        self.storage.cleanup_old_blocks(keep_blocks)
    
    def _start_monitoring(self):
        """Запуск мониторинга ноды"""
        if self.monitor_thread and self.monitor_thread.is_alive():
            return
        
        self.shutdown_event.clear()
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        logger.info("Мониторинг ноды запущен")
    
    def _stop_monitoring(self):
        """Остановка мониторинга ноды"""
        if self.monitor_thread:
            self.shutdown_event.set()
            self.monitor_thread.join(timeout=5)
            self.monitor_thread = None
            logger.info("Мониторинг ноды остановлен")
    
    def _monitor_loop(self):
        """Цикл мониторинга ноды"""
        while not self.shutdown_event.is_set():
            try:
                # Обновление статуса
                self._update_status()
                
                # Проверка синхронизации
                self._check_sync_status()
                
                # Пауза между проверками
                time.sleep(10)
                
            except Exception as e:
                logger.error(f"Ошибка в цикле мониторинга: {e}")
                time.sleep(30)  # Увеличенная пауза при ошибке
    
    def _update_status(self):
        """Обновление статуса ноды"""
        if not self.is_running():
            self.status.is_running = False
            self.status.is_syncing = False
            return
        
        # Обновление времени работы
        if self.geth_process:
            self.status.uptime_seconds = int(time.time() - self.geth_process.start_time)
    
    def _check_sync_status(self):
        """Проверка статуса синхронизации"""
        try:
            # Здесь можно добавить RPC вызовы для проверки синхронизации
            # Пока используем простую эмуляцию
            if self.status.is_running:
                # Эмуляция получения информации о синхронизации
                self.status.is_syncing = False  # В реальности получаем через RPC
                self.status.peer_count = 0      # В реальности получаем через RPC
                
        except Exception as e:
            logger.error(f"Ошибка проверки статуса синхронизации: {e}")
    
    def health_check(self) -> Dict[str, Any]:
        """
        Проверка здоровья ноды
        
        Returns:
            Результат проверки здоровья
        """
        status = self.get_status()
        storage_stats = self.get_storage_statistics()
        
        health = {
            "status": "healthy" if status.is_running else "unhealthy",
            "is_running": status.is_running,
            "is_syncing": status.is_syncing,
            "uptime_seconds": status.uptime_seconds,
            "peer_count": status.peer_count,
            "current_block": status.current_block,
            "storage": storage_stats,
            "last_error": status.last_error,
            "timestamp": time.time()
        }
        
        # Определение статуса здоровья
        if not status.is_running:
            health["status"] = "unhealthy"
        elif status.last_error:
            health["status"] = "degraded"
        elif storage_stats["usage_percent"] > 90:
            health["status"] = "warning"
        
        return health
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Получение метрик ноды
        
        Returns:
            Метрики ноды
        """
        status = self.get_status()
        storage_stats = self.get_storage_statistics()
        
        return {
            "ethereum_node_running": 1 if status.is_running else 0,
            "ethereum_node_syncing": 1 if status.is_syncing else 0,
            "ethereum_node_uptime_seconds": status.uptime_seconds,
            "ethereum_node_peer_count": status.peer_count,
            "ethereum_node_current_block": status.current_block or 0,
            "ethereum_storage_blocks_total": storage_stats["total_blocks"],
            "ethereum_storage_blocks_max": storage_stats["max_blocks"],
            "ethereum_storage_size_bytes": storage_stats["storage_size_bytes"],
            "ethereum_storage_usage_percent": storage_stats["usage_percent"]
        }
    
    def __enter__(self):
        """Контекстный менеджер - вход"""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Контекстный менеджер - выход"""
        self.stop()
    
    def __str__(self) -> str:
        """Строковое представление"""
        status = self.get_status()
        return f"EthereumNode(running={status.is_running}, syncing={status.is_syncing}, uptime={status.uptime_seconds}s)"
    
    def __repr__(self) -> str:
        """Представление для отладки"""
        return self.__str__() 