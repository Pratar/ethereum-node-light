"""
Ethereum Block Storage

Module for managing block storage with 100 block limit.
"""

import os
import json
import shutil
from typing import List, Dict, Any, Optional
from collections import deque
import logging

logger = logging.getLogger(__name__)


class BlockStorage:
    """Block storage with limit"""
    
    def __init__(self, data_dir: str = "/data", max_blocks: int = 100):
        """
        Initialize block storage
        
        Args:
            data_dir: Data storage directory
            max_blocks: Maximum number of blocks
        """
        self.data_dir = data_dir
        self.max_blocks = max_blocks
        self.blocks_dir = os.path.join(data_dir, "blocks")
        self.metadata_file = os.path.join(data_dir, "metadata.json")
        
        # Queue for tracking blocks (FIFO)
        self.block_queue = deque(maxlen=max_blocks)
        
        # Metadata
        self.metadata = {
            "total_blocks": 0,
            "max_blocks": max_blocks,
            "oldest_block": None,
            "newest_block": None,
            "storage_size_bytes": 0
        }
        
        self._ensure_directories()
        self._load_metadata()
    
    def _ensure_directories(self):
        """Create necessary directories"""
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.blocks_dir, exist_ok=True)
    
    def _load_metadata(self):
        """Load metadata from file"""
        if os.path.exists(self.metadata_file):
            try:
                with open(self.metadata_file, 'r') as f:
                    self.metadata = json.load(f)
                
                # Rebuild block queue
                self._rebuild_queue()
                logger.info(f"Metadata loaded: {self.metadata['total_blocks']} blocks")
            except Exception as e:
                logger.error(f"Error loading metadata: {e}")
                self._save_metadata()
    
    def _save_metadata(self):
        """Save metadata to file"""
        try:
            with open(self.metadata_file, 'w') as f:
                json.dump(self.metadata, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving metadata: {e}")
    
    def _rebuild_queue(self):
        """Rebuild block queue"""
        self.block_queue.clear()
        
        # Scan blocks directory
        if os.path.exists(self.blocks_dir):
            block_files = []
            for filename in os.listdir(self.blocks_dir):
                if filename.endswith('.json'):
                    try:
                        block_number = int(filename.replace('.json', ''))
                        block_files.append((block_number, filename))
                    except ValueError:
                        continue
            
            # Sort by block number
            block_files.sort(key=lambda x: x[0])
            
            # Add to queue
            for block_number, filename in block_files:
                self.block_queue.append(block_number)
    
    def add_block(self, block_number: int, block_data: Dict[str, Any]) -> bool:
        """
        Добавление блока в хранилище
        
        Args:
            block_number: Номер блока
            block_data: Данные блока
            
        Returns:
            True если блок добавлен, False если уже существует
        """
        if self.has_block(block_number):
            logger.debug(f"Блок {block_number} уже существует")
            return False
        
        # Проверка лимита блоков
        if len(self.block_queue) >= self.max_blocks:
            self._remove_oldest_block()
        
        # Сохранение блока
        block_file = os.path.join(self.blocks_dir, f"{block_number}.json")
        try:
            with open(block_file, 'w') as f:
                json.dump(block_data, f, indent=2)
            
            # Обновление очереди и метаданных
            self.block_queue.append(block_number)
            self._update_metadata()
            
            logger.info(f"Блок {block_number} добавлен")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка сохранения блока {block_number}: {e}")
            return False
    
    def get_block(self, block_number: int) -> Optional[Dict[str, Any]]:
        """
        Получение блока по номеру
        
        Args:
            block_number: Номер блока
            
        Returns:
            Данные блока или None если не найден
        """
        if not self.has_block(block_number):
            return None
        
        block_file = os.path.join(self.blocks_dir, f"{block_number}.json")
        try:
            with open(block_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Ошибка чтения блока {block_number}: {e}")
            return None
    
    def has_block(self, block_number: int) -> bool:
        """
        Проверка наличия блока
        
        Args:
            block_number: Номер блока
            
        Returns:
            True если блок существует
        """
        block_file = os.path.join(self.blocks_dir, f"{block_number}.json")
        return os.path.exists(block_file)
    
    def remove_block(self, block_number: int) -> bool:
        """
        Удаление блока
        
        Args:
            block_number: Номер блока
            
        Returns:
            True если блок удален
        """
        if not self.has_block(block_number):
            return False
        
        block_file = os.path.join(self.blocks_dir, f"{block_number}.json")
        try:
            os.remove(block_file)
            
            # Удаление из очереди
            if block_number in self.block_queue:
                self.block_queue.remove(block_number)
            
            self._update_metadata()
            logger.info(f"Блок {block_number} удален")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка удаления блока {block_number}: {e}")
            return False
    
    def _remove_oldest_block(self):
        """Удаление самого старого блока"""
        if not self.block_queue:
            return
        
        oldest_block = self.block_queue[0]
        self.remove_block(oldest_block)
        logger.info(f"Удален самый старый блок: {oldest_block}")
    
    def _update_metadata(self):
        """Обновление метаданных"""
        self.metadata["total_blocks"] = len(self.block_queue)
        self.metadata["oldest_block"] = self.block_queue[0] if self.block_queue else None
        self.metadata["newest_block"] = self.block_queue[-1] if self.block_queue else None
        self.metadata["storage_size_bytes"] = self._calculate_storage_size()
        
        self._save_metadata()
    
    def _calculate_storage_size(self) -> int:
        """Вычисление размера хранилища в байтах"""
        total_size = 0
        
        if os.path.exists(self.blocks_dir):
            for filename in os.listdir(self.blocks_dir):
                file_path = os.path.join(self.blocks_dir, filename)
                if os.path.isfile(file_path):
                    total_size += os.path.getsize(file_path)
        
        # Добавляем размер метаданных
        if os.path.exists(self.metadata_file):
            total_size += os.path.getsize(self.metadata_file)
        
        return total_size
    
    def get_blocks_range(self, start_block: int, end_block: int) -> List[Dict[str, Any]]:
        """
        Получение диапазона блоков
        
        Args:
            start_block: Начальный номер блока
            end_block: Конечный номер блока
            
        Returns:
            Список блоков в диапазоне
        """
        blocks = []
        for block_number in range(start_block, end_block + 1):
            block_data = self.get_block(block_number)
            if block_data:
                blocks.append(block_data)
        
        return blocks
    
    def get_all_blocks(self) -> List[Dict[str, Any]]:
        """
        Получение всех блоков
        
        Returns:
            Список всех блоков
        """
        return self.get_blocks_range(
            self.metadata["oldest_block"] or 0,
            self.metadata["newest_block"] or 0
        )
    
    def get_block_numbers(self) -> List[int]:
        """
        Получение списка номеров блоков
        
        Returns:
            Список номеров блоков
        """
        return list(self.block_queue)
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Получение статистики хранилища
        
        Returns:
            Статистика хранилища
        """
        return {
            "total_blocks": self.metadata["total_blocks"],
            "max_blocks": self.metadata["max_blocks"],
            "oldest_block": self.metadata["oldest_block"],
            "newest_block": self.metadata["newest_block"],
            "storage_size_bytes": self.metadata["storage_size_bytes"],
            "storage_size_mb": round(self.metadata["storage_size_bytes"] / (1024 * 1024), 2),
            "usage_percent": round((self.metadata["total_blocks"] / self.metadata["max_blocks"]) * 100, 2)
        }
    
    def clear(self):
        """Очистка всего хранилища"""
        try:
            # Удаление всех файлов блоков
            if os.path.exists(self.blocks_dir):
                shutil.rmtree(self.blocks_dir)
                os.makedirs(self.blocks_dir)
            
            # Очистка очереди
            self.block_queue.clear()
            
            # Сброс метаданных
            self.metadata.update({
                "total_blocks": 0,
                "oldest_block": None,
                "newest_block": None,
                "storage_size_bytes": 0
            })
            
            self._save_metadata()
            logger.info("Хранилище очищено")
            
        except Exception as e:
            logger.error(f"Ошибка очистки хранилища: {e}")
    
    def cleanup_old_blocks(self, keep_blocks: int = None):
        """
        Очистка старых блоков
        
        Args:
            keep_blocks: Количество блоков для сохранения (по умолчанию max_blocks)
        """
        if keep_blocks is None:
            keep_blocks = self.max_blocks
        
        if len(self.block_queue) <= keep_blocks:
            return
        
        # Удаление лишних блоков
        blocks_to_remove = len(self.block_queue) - keep_blocks
        for _ in range(blocks_to_remove):
            self._remove_oldest_block()
        
        logger.info(f"Удалено {blocks_to_remove} старых блоков")
    
    def __len__(self) -> int:
        """Количество блоков в хранилище"""
        return len(self.block_queue)
    
    def __contains__(self, block_number: int) -> bool:
        """Проверка наличия блока"""
        return self.has_block(block_number)
    
    def __str__(self) -> str:
        """Строковое представление"""
        stats = self.get_statistics()
        return f"BlockStorage(blocks={stats['total_blocks']}/{stats['max_blocks']}, size={stats['storage_size_mb']}MB)"
    
    def __repr__(self) -> str:
        """Представление для отладки"""
        return self.__str__() 