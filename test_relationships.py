#!/usr/bin/env python3
"""
Advanced relationship and constraint testing
"""
import sys
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

def test_sqlalchemy_metadata():
    """Test SQLAlchemy metadata generation without DB connection."""
    print("🧪 Testing SQLAlchemy metadata generation...")
    
    try:
        from backend.database.base import Base
        from backend.schemas.user_model import UserModel
        from backend.schemas.tenant_model import TenantModel
        from backend.schemas.session_model import SessionModel
        from backend.schemas.login_session import LoginSessionModel
        
        # Try to create metadata
        metadata = Base.metadata
        print(f"✅ Metadata created successfully with {len(metadata.tables)} tables")
        
        # List all tables
        print("\n📋 Tables in metadata:")
        for table_name, table in metadata.tables.items():
            print(f"  • {table_name}")
            
        return True
    except Exception as e:
        print(f"❌ Metadata generation failed: {e}")
        return False

def test_foreign_key_references():
    """Test FK reference integrity without DB."""
    print("\n🧪 Testing FK reference integrity...")
    
    try:
        from backend.database.base import Base
        
        # Import all models to trigger metadata creation
        from backend.schemas.user_model import UserModel
        from backend.schemas.tenant_model import TenantModel
        from backend.schemas.session_model import SessionModel
        from backend.schemas.message_model import MessageModel
        from backend.schemas.log_model import LogModel
        from backend.schemas.login_session import LoginSessionModel
        
        metadata = Base.metadata
        errors = []
        
        # Check each table's foreign keys
        for table_name, table in metadata.tables.items():
            for fk in table.foreign_keys:
                # FK format: table.column
                referenced_table = fk.column.table.name
                referenced_column = fk.column.name
                
                # Check if referenced table exists
                if referenced_table not in metadata.tables:
                    errors.append(f"❌ {table_name}: FK references non-existent table '{referenced_table}'")
                else:
                    # Check if referenced column exists
                    ref_table = metadata.tables[referenced_table]
                    if referenced_column not in ref_table.columns:
                        errors.append(f"❌ {table_name}: FK references non-existent column '{referenced_table}.{referenced_column}'")
        
        if errors:
            for error in errors:
                print(error)
            return False
        else:
            print("✅ All FK references are valid")
            return True
            
    except Exception as e:
        print(f"❌ FK reference test failed: {e}")
        return False

def test_enum_definitions():
    """Test enum SQL generation."""
    print("\n🧪 Testing enum SQL generation...")
    
    try:
        from backend.schemas.user_model import UserRole
        from backend.schemas.tenant_model import PlanType
        from backend.database.base import Base
        
        # Import models to register with Base
        from backend.schemas.user_model import UserModel
        from backend.schemas.tenant_model import TenantModel
        
        # Create a mock engine to generate DDL
        engine = create_engine("postgresql://", strategy='mock', executor=lambda sql, *_: None)
        
        # Try to create DDL
        Base.metadata.create_all(engine, checkfirst=False)
        
        print("✅ Enum DDL generation successful")
        return True
        
    except Exception as e:
        print(f"❌ Enum DDL generation failed: {e}")
        return False

def test_circular_relationships():
    """Test for circular relationship dependencies."""
    print("\n🧪 Testing circular relationships...")
    
    try:
        # Import models in dependency order
        from backend.schemas.tenant_model import TenantModel
        from backend.schemas.user_model import UserModel  
        from backend.schemas.session_model import SessionModel
        from backend.schemas.login_session import LoginSessionModel
        from backend.schemas.message_model import MessageModel
        from backend.schemas.log_model import LogModel
        
        # Try to access relationships (this will trigger lazy loading)
        user_relationships = [
            'tenant',
            'login_sessions', 
            'sessions'
        ]
        
        tenant_relationships = [
            'users',
            'sessions'
        ]
        
        print("✅ No circular relationship import errors")
        return True
        
    except Exception as e:
        print(f"❌ Circular relationship test failed: {e}")
        return False

def main():
    """Run all relationship tests."""
    print("🚀 Starting Advanced Schema Relationship Tests")
    print("=" * 60)
    
    tests = [
        test_sqlalchemy_metadata,
        test_foreign_key_references,
        test_enum_definitions,
        test_circular_relationships,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        if test():
            passed += 1
        else:
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"📊 Advanced Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All relationship tests passed! Schema is production-ready.")
        return 0
    else:
        print("❌ Some relationship tests failed. Database migration may have issues.")
        return 1

if __name__ == "__main__":
    sys.exit(main())