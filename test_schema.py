#!/usr/bin/env python3
"""
Schema validation test script - Tests models without database connection
"""
import sys
import os
from typing import Optional

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

def test_model_imports():
    """Test that all models can be imported without errors."""
    print("🧪 Testing model imports...")
    
    try:
        from backend.schemas.user_model import UserModel, UserRole
        from backend.schemas.tenant_model import TenantModel, PlanType
        from backend.schemas.session_model import SessionModel
        from backend.schemas.message_model import MessageModel
        from backend.schemas.log_model import LogModel
        from backend.schemas.login_session import LoginSessionModel
        print("✅ All models imported successfully")
        return True
    except Exception as e:
        print(f"❌ Model import failed: {e}")
        return False

def test_enum_values():
    """Test enum definitions."""
    print("\n🧪 Testing enum values...")
    
    try:
        from backend.schemas.user_model import UserRole
        from backend.schemas.tenant_model import PlanType
        
        # Test UserRole enum
        assert UserRole.user == "user"
        assert UserRole.admin == "admin"
        print("✅ UserRole enum values correct")
        
        # Test PlanType enum
        assert PlanType.free == "free"
        assert PlanType.pro == "pro"
        assert PlanType.enterprise == "enterprise"
        print("✅ PlanType enum values correct")
        
        return True
    except Exception as e:
        print(f"❌ Enum test failed: {e}")
        return False

def test_model_attributes():
    """Test model column definitions."""
    print("\n🧪 Testing model attributes...")
    
    try:
        from backend.schemas.user_model import UserModel
        from backend.schemas.login_session import LoginSessionModel
        
        # Test UserModel has required columns
        assert hasattr(UserModel, 'id')
        assert hasattr(UserModel, 'role')
        assert hasattr(UserModel, 'username')
        assert hasattr(UserModel, 'email')
        assert hasattr(UserModel, 'tenant_id')
        print("✅ UserModel attributes correct")
        
        # Test LoginSessionModel has required columns
        assert hasattr(LoginSessionModel, 'id')
        assert hasattr(LoginSessionModel, 'user_id')
        assert hasattr(LoginSessionModel, 'created_at')
        assert hasattr(LoginSessionModel, 'expires_at')
        print("✅ LoginSessionModel attributes correct")
        
        return True
    except Exception as e:
        print(f"❌ Model attributes test failed: {e}")
        return False

def test_relationships():
    """Test relationship definitions."""
    print("\n🧪 Testing relationships...")
    
    try:
        from backend.schemas.user_model import UserModel
        from backend.schemas.tenant_model import TenantModel
        from backend.schemas.session_model import SessionModel
        from backend.schemas.login_session import LoginSessionModel
        
        # Test UserModel relationships
        assert hasattr(UserModel, 'tenant')
        assert hasattr(UserModel, 'login_sessions')
        assert hasattr(UserModel, 'sessions')
        print("✅ UserModel relationships correct")
        
        # Test TenantModel relationships
        assert hasattr(TenantModel, 'users')
        assert hasattr(TenantModel, 'sessions')
        print("✅ TenantModel relationships correct")
        
        # Test LoginSessionModel relationships
        assert hasattr(LoginSessionModel, 'user')
        print("✅ LoginSessionModel relationships correct")
        
        return True
    except Exception as e:
        print(f"❌ Relationships test failed: {e}")
        return False

def test_table_names():
    """Test table names are correctly set."""
    print("\n🧪 Testing table names...")
    
    try:
        from backend.schemas.user_model import UserModel
        from backend.schemas.tenant_model import TenantModel
        from backend.schemas.session_model import SessionModel
        from backend.schemas.message_model import MessageModel
        from backend.schemas.log_model import LogModel
        from backend.schemas.login_session import LoginSessionModel
        
        assert UserModel.__tablename__ == "users"
        assert TenantModel.__tablename__ == "tenant"
        assert SessionModel.__tablename__ == "session"
        assert MessageModel.__tablename__ == "message"
        assert LogModel.__tablename__ == "log"
        assert LoginSessionModel.__tablename__ == "login_session"
        
        print("✅ All table names correct")
        return True
    except Exception as e:
        print(f"❌ Table names test failed: {e}")
        return False

def main():
    """Run all schema tests."""
    print("🚀 Starting MevzuSağlık Schema Tests")
    print("=" * 50)
    
    tests = [
        test_model_imports,
        test_enum_values,
        test_model_attributes,
        test_relationships,
        test_table_names,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        if test():
            passed += 1
        else:
            failed += 1
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All schema tests passed! Models are ready for migration.")
        return 0
    else:
        print("❌ Some tests failed. Please fix the issues before proceeding.")
        return 1

if __name__ == "__main__":
    sys.exit(main())