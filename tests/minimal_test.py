#!/usr/bin/env python3
"""
Minimal test suite for TrueNAS MCP Server
Runs without pytest or other test dependencies
"""

import os
import sys
import asyncio
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import truenas_mcp_server

# Test counter
tests_run = 0
tests_passed = 0

def test(name):
    """Simple test decorator"""
    def decorator(func):
        async def wrapper():
            global tests_run, tests_passed
            tests_run += 1
            try:
                await func()
                tests_passed += 1
                print(f"✅ {name}")
            except Exception as e:
                print(f"❌ {name}: {e}")
        return wrapper
    return decorator

@test("Import module")
async def test_import():
    """Test that the module imports successfully"""
    assert truenas_mcp_server is not None
    assert hasattr(truenas_mcp_server, 'mcp')

@test("Check core functions exist")
async def test_functions_exist():
    """Test that core functions are defined"""
    functions = [
        'list_users', 'get_user', 'get_system_info',
        'list_pools', 'list_datasets', 'create_dataset',
        'list_smb_shares', 'create_smb_share', 'create_snapshot'
    ]
    for func in functions:
        assert hasattr(truenas_mcp_server, func), f"Missing function: {func}"

@test("Check Phase 2 functions exist")
async def test_phase2_functions():
    """Test that Phase 2 functions are defined"""
    functions = [
        'modify_dataset_permissions', 'update_dataset_acl',
        'get_dataset_permissions', 'modify_dataset_properties',
        'get_dataset_properties', 'create_nfs_export',
        'create_iscsi_target', 'create_snapshot_policy'
    ]
    for func in functions:
        assert hasattr(truenas_mcp_server, func), f"Missing Phase 2 function: {func}"

@test("Environment configuration")
async def test_environment():
    """Test environment variable handling"""
    # Mock environment
    with patch.dict(os.environ, {
        'TRUENAS_URL': 'https://test.local',
        'TRUENAS_API_KEY': 'test-key',
        'TRUENAS_VERIFY_SSL': 'false'
    }):
        # Should be able to get client config
        assert os.getenv('TRUENAS_URL') == 'https://test.local'
        assert os.getenv('TRUENAS_API_KEY') == 'test-key'
        assert os.getenv('TRUENAS_VERIFY_SSL') == 'false'

@test("Debug connection function")
async def test_debug_connection():
    """Test debug_connection function"""
    with patch.dict(os.environ, {
        'TRUENAS_URL': 'https://test.local',
        'TRUENAS_API_KEY': 'test-key'
    }):
        result = await truenas_mcp_server.debug_connection()
        assert 'environment' in result
        assert 'client_status' in result

@test("Parse size helper function")
async def test_parse_size():
    """Test the _parse_size helper function"""
    parse_size = truenas_mcp_server._parse_size
    
    assert parse_size("1K") == 1024
    assert parse_size("1M") == 1024 * 1024
    assert parse_size("1G") == 1024 * 1024 * 1024
    assert parse_size("100") == 100  # No unit means bytes

@test("List users with mock")
async def test_list_users_mock():
    """Test list_users with mocked HTTP client"""
    # Mock the HTTP client
    mock_client = AsyncMock()
    mock_response = Mock()
    mock_response.json.return_value = [
        {"id": 1, "username": "root", "uid": 0},
        {"id": 2, "username": "admin", "uid": 1000}
    ]
    mock_response.raise_for_status = Mock()
    mock_client.get.return_value = mock_response
    
    # Patch get_client to return our mock
    with patch('truenas_mcp_server.get_client', return_value=mock_client):
        result = await truenas_mcp_server.list_users()
        
        assert result['success'] is True
        assert 'users' in result
        assert len(result['users']) == 2
        assert result['users'][0]['username'] == 'root'

@test("Error handling")
async def test_error_handling():
    """Test that functions handle errors gracefully"""
    # Mock client that raises an error
    mock_client = AsyncMock()
    mock_client.get.side_effect = Exception("Connection error")
    
    with patch('truenas_mcp_server.get_client', return_value=mock_client):
        result = await truenas_mcp_server.list_users()
        
        assert result['success'] is False
        assert 'error' in result
        assert 'Connection error' in result['error']

async def run_tests():
    """Run all tests"""
    print("🧪 Running TrueNAS MCP Server Tests")
    print("=" * 40)
    
    # Collect all test functions
    test_functions = [
        test_import(),
        test_functions_exist(),
        test_phase2_functions(),
        test_environment(),
        test_debug_connection(),
        test_parse_size(),
        test_list_users_mock(),
        test_error_handling(),
    ]
    
    # Run all tests
    for test_func in test_functions:
        await test_func
    
    print("=" * 40)
    print(f"Tests run: {tests_run}")
    print(f"Tests passed: {tests_passed}")
    print(f"Tests failed: {tests_run - tests_passed}")
    
    if tests_passed == tests_run:
        print("\n✅ All tests passed!")
        return 0
    else:
        print(f"\n❌ {tests_run - tests_passed} tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(asyncio.run(run_tests()))
