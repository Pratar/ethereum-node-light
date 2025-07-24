"""
Unit tests for Ethereum block storage module
"""

import pytest
import os
import json
import tempfile
import shutil
from unittest.mock import patch

from src.ethereum.storage import BlockStorage


class TestBlockStorage:
    """Tests for BlockStorage class"""
    
    @pytest.fixture
    def temp_dir(self):
        """Temporary directory for tests"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.fixture
    def storage(self, temp_dir):
        """Storage instance for tests"""
        return BlockStorage(temp_dir, max_blocks=5)
    
    def test_initialization(self, temp_dir):
        """Test storage initialization"""
        storage = BlockStorage(temp_dir, max_blocks=10)
        
        assert storage.data_dir == temp_dir
        assert storage.max_blocks == 10
        assert storage.blocks_dir == os.path.join(temp_dir, "blocks")
        assert storage.metadata_file == os.path.join(temp_dir, "metadata.json")
        assert len(storage.block_queue) == 0
        
        # Check directory creation
        assert os.path.exists(temp_dir)
        assert os.path.exists(storage.blocks_dir)
    
    def test_add_block(self, storage):
        """Test adding block"""
        block_data = {"number": 1, "hash": "0x123", "transactions": []}
        
        result = storage.add_block(1, block_data)
        
        assert result is True
        assert storage.has_block(1)
        assert len(storage.block_queue) == 1
        assert 1 in storage.block_queue
        
        # Check file saving
        block_file = os.path.join(storage.blocks_dir, "1.json")
        assert os.path.exists(block_file)
        
        with open(block_file, 'r') as f:
            saved_data = json.load(f)
        
        assert saved_data == block_data
    
    def test_add_duplicate_block(self, storage):
        """Test adding duplicate block"""
        block_data = {"number": 1, "hash": "0x123"}
        
        # Add block first time
        result1 = storage.add_block(1, block_data)
        assert result1 is True
        
        # Add same block second time
        result2 = storage.add_block(1, block_data)
        assert result2 is False
        
        # Check that only one block in queue
        assert len(storage.block_queue) == 1
    
    def test_get_block(self, storage):
        """Test getting block"""
        block_data = {"number": 2, "hash": "0x456", "timestamp": 1234567890}
        
        # Add block
        storage.add_block(2, block_data)
        
        # Get block
        retrieved_data = storage.get_block(2)
        
        assert retrieved_data == block_data
    
    def test_get_nonexistent_block(self, storage):
        """Test getting non-existent block"""
        result = storage.get_block(999)
        assert result is None
    
    def test_has_block(self, storage):
        """Test checking block existence"""
        block_data = {"number": 3, "hash": "0x789"}
        
        # Блок не существует
        assert storage.has_block(3) is False
        
        # Добавляем блок
        storage.add_block(3, block_data)
        
        # Блок существует
        assert storage.has_block(3) is True
    
    def test_remove_block(self, storage):
        """Тест удаления блока"""
        block_data = {"number": 4, "hash": "0xabc"}
        
        # Добавляем блок
        storage.add_block(4, block_data)
        assert storage.has_block(4) is True
        
        # Удаляем блок
        result = storage.remove_block(4)
        assert result is True
        assert storage.has_block(4) is False
        assert 4 not in storage.block_queue
        
        # Проверяем удаление файла
        block_file = os.path.join(storage.blocks_dir, "4.json")
        assert not os.path.exists(block_file)
    
    def test_remove_nonexistent_block(self, storage):
        """Тест удаления несуществующего блока"""
        result = storage.remove_block(999)
        assert result is False
    
    def test_block_limit_enforcement(self, storage):
        """Тест соблюдения лимита блоков"""
        # Добавляем 5 блоков (максимум)
        for i in range(1, 6):
            block_data = {"number": i, "hash": f"0x{i:03x}"}
            storage.add_block(i, block_data)
        
        assert len(storage.block_queue) == 5
        
        # Добавляем еще один блок - должен удалиться самый старый
        block_data = {"number": 6, "hash": "0x006"}
        storage.add_block(6, block_data)
        
        # Проверяем, что старый блок удален
        assert len(storage.block_queue) == 5
        assert 1 not in storage.block_queue  # Самый старый блок удален
        assert 6 in storage.block_queue      # Новый блок добавлен
        
        # Проверяем, что файл старого блока удален
        old_block_file = os.path.join(storage.blocks_dir, "1.json")
        assert not os.path.exists(old_block_file)
        
        # Проверяем, что файл нового блока создан
        new_block_file = os.path.join(storage.blocks_dir, "6.json")
        assert os.path.exists(new_block_file)
    
    def test_get_blocks_range(self, storage):
        """Тест получения диапазона блоков"""
        # Добавляем несколько блоков
        for i in range(1, 6):
            block_data = {"number": i, "hash": f"0x{i:03x}"}
            storage.add_block(i, block_data)
        
        # Получаем диапазон
        blocks = storage.get_blocks_range(2, 4)
        
        assert len(blocks) == 3
        assert blocks[0]["number"] == 2
        assert blocks[1]["number"] == 3
        assert blocks[2]["number"] == 4
    
    def test_get_blocks_range_with_missing(self, storage):
        """Тест получения диапазона с отсутствующими блоками"""
        # Добавляем только четные блоки
        for i in range(2, 8, 2):
            block_data = {"number": i, "hash": f"0x{i:03x}"}
            storage.add_block(i, block_data)
        
        # Получаем диапазон с отсутствующими блоками
        blocks = storage.get_blocks_range(1, 6)
        
        assert len(blocks) == 3  # Только блоки 2, 4, 6
        block_numbers = [block["number"] for block in blocks]
        assert block_numbers == [2, 4, 6]
    
    def test_get_all_blocks(self, storage):
        """Тест получения всех блоков"""
        # Добавляем несколько блоков
        for i in range(1, 4):
            block_data = {"number": i, "hash": f"0x{i:03x}"}
            storage.add_block(i, block_data)
        
        # Получаем все блоки
        blocks = storage.get_all_blocks()
        
        assert len(blocks) == 3
        block_numbers = [block["number"] for block in blocks]
        assert block_numbers == [1, 2, 3]
    
    def test_get_block_numbers(self, storage):
        """Тест получения списка номеров блоков"""
        # Добавляем несколько блоков
        for i in range(1, 4):
            block_data = {"number": i, "hash": f"0x{i:03x}"}
            storage.add_block(i, block_data)
        
        # Получаем номера блоков
        block_numbers = storage.get_block_numbers()
        
        assert block_numbers == [1, 2, 3]
    
    def test_get_statistics(self, storage):
        """Тест получения статистики"""
        # Добавляем несколько блоков
        for i in range(1, 4):
            block_data = {"number": i, "hash": f"0x{i:03x}"}
            storage.add_block(i, block_data)
        
        # Получаем статистику
        stats = storage.get_statistics()
        
        assert stats["total_blocks"] == 3
        assert stats["max_blocks"] == 5
        assert stats["oldest_block"] == 1
        assert stats["newest_block"] == 3
        assert stats["storage_size_bytes"] >= 0
        assert stats["storage_size_mb"] >= 0
        assert stats["usage_percent"] == 60.0  # 3/5 * 100
    
    def test_clear(self, storage):
        """Тест очистки хранилища"""
        # Добавляем несколько блоков
        for i in range(1, 4):
            block_data = {"number": i, "hash": f"0x{i:03x}"}
            storage.add_block(i, block_data)
        
        assert len(storage.block_queue) == 3
        
        # Очищаем хранилище
        storage.clear()
        
        assert len(storage.block_queue) == 0
        assert storage.get_statistics()["total_blocks"] == 0
        
        # Проверяем, что директория блоков пуста
        assert len(os.listdir(storage.blocks_dir)) == 0
    
    def test_cleanup_old_blocks(self, storage):
        """Тест очистки старых блоков"""
        # Добавляем 5 блоков
        for i in range(1, 6):
            block_data = {"number": i, "hash": f"0x{i:03x}"}
            storage.add_block(i, block_data)
        
        assert len(storage.block_queue) == 5
        
        # Очищаем, оставляя только 3 блока
        storage.cleanup_old_blocks(keep_blocks=3)
        
        assert len(storage.block_queue) == 3
        # Должны остаться самые новые блоки
        assert list(storage.block_queue) == [3, 4, 5]
    
    def test_metadata_persistence(self, temp_dir):
        """Тест сохранения и загрузки метаданных"""
        # Создаем хранилище и добавляем блоки
        storage1 = BlockStorage(temp_dir, max_blocks=3)
        for i in range(1, 4):
            block_data = {"number": i, "hash": f"0x{i:03x}"}
            storage1.add_block(i, block_data)
        
        # Создаем новое хранилище в той же директории
        storage2 = BlockStorage(temp_dir, max_blocks=3)
        
        # Проверяем, что метаданные загружены
        assert len(storage2.block_queue) == 3
        assert storage2.has_block(1)
        assert storage2.has_block(2)
        assert storage2.has_block(3)
        
        stats = storage2.get_statistics()
        assert stats["total_blocks"] == 3
        assert stats["oldest_block"] == 1
        assert stats["newest_block"] == 3
    
    def test_len_operator(self, storage):
        """Тест оператора len"""
        assert len(storage) == 0
        
        # Добавляем блоки
        for i in range(1, 4):
            block_data = {"number": i, "hash": f"0x{i:03x}"}
            storage.add_block(i, block_data)
        
        assert len(storage) == 3
    
    def test_contains_operator(self, storage):
        """Тест оператора in"""
        block_data = {"number": 5, "hash": "0x005"}
        storage.add_block(5, block_data)
        
        assert 5 in storage
        assert 999 not in storage
    
    def test_string_representation(self, storage):
        """Тест строкового представления"""
        # Пустое хранилище
        storage_str = str(storage)
        assert "BlockStorage" in storage_str
        assert "blocks=0/5" in storage_str
        
        # Добавляем блок
        block_data = {"number": 1, "hash": "0x001"}
        storage.add_block(1, block_data)
        
        storage_str = str(storage)
        assert "blocks=1/5" in storage_str
    
    def test_repr_representation(self, storage):
        """Тест представления для отладки"""
        storage_repr = repr(storage)
        assert storage_repr == str(storage)
    
    def test_error_handling(self, storage):
        """Тест обработки ошибок"""
        # Тест с некорректными данными блока
        with patch('json.dump') as mock_dump:
            mock_dump.side_effect = Exception("JSON error")
            
            result = storage.add_block(1, {"number": 1})
            assert result is False
        
        # Тест с некорректным файлом блока
        with patch('builtins.open') as mock_open:
            mock_open.side_effect = Exception("File error")
            
            result = storage.get_block(1)
            assert result is None
    
    def test_concurrent_access(self, storage):
        """Тест конкурентного доступа"""
        import threading
        import time
        
        def add_blocks():
            for i in range(10, 20):
                block_data = {"number": i, "hash": f"0x{i:03x}"}
                storage.add_block(i, block_data)
                time.sleep(0.01)
        
        def remove_blocks():
            for i in range(10, 20):
                storage.remove_block(i)
                time.sleep(0.01)
        
        # Запускаем потоки
        thread1 = threading.Thread(target=add_blocks)
        thread2 = threading.Thread(target=remove_blocks)
        
        thread1.start()
        thread2.start()
        
        thread1.join()
        thread2.join()
        
        # Проверяем, что хранилище в корректном состоянии
        stats = storage.get_statistics()
        assert stats["total_blocks"] <= storage.max_blocks 