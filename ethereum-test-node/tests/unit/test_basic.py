import pytest
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))

def test_import_ethereum():
    """Test importing ethereum module"""
    try:
        import ethereum
        assert True
    except ImportError:
        pytest.fail("Failed to import ethereum module")

def test_import_monitoring():
    """Test importing monitoring module"""
    try:
        import monitoring
        assert True
    except ImportError:
        pytest.fail("Failed to import monitoring module")

def test_basic_math():
    """Simple math test"""
    assert 2 + 2 == 4
    assert 10 - 5 == 5
    assert 3 * 4 == 12
    assert 15 / 3 == 5

def test_string_operations():
    """Test string operations"""
    test_string = "Ethereum Test Node"
    assert len(test_string) == 18
    assert "Ethereum" in test_string
    assert test_string.upper() == "ETHEREUM TEST NODE"
