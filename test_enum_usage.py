#!/usr/bin/env python3
"""
Test enum usage in the entire codebase
"""
import sys
import os
from unittest.mock import Mock

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

def test_plan_limits_access():
    """Test PLAN_LIMITS dictionary access with enum values."""
    print("🧪 Testing PLAN_LIMITS access with enum values...")
    
    try:
        from backend.schemas.tenant_model import PlanType
        from backend.dependencies.auth import PLAN_LIMITS
        
        # Test direct enum value access
        for plan_type in PlanType:
            plan_key = plan_type.value
            if plan_key in PLAN_LIMITS:
                limit = PLAN_LIMITS[plan_key]["requests_per_day"]
                print(f"  ✅ {plan_key}: {limit} requests/day")
            else:
                print(f"  ❌ {plan_key}: NOT FOUND in PLAN_LIMITS")
                return False
        
        return True
    except Exception as e:
        print(f"❌ PLAN_LIMITS test failed: {e}")
        return False

def test_quota_function():
    """Test quota check function with mock tenant."""
    print("\n🧪 Testing quota check function...")
    
    try:
        from backend.dependencies.quota import check_daily_quota
        from backend.schemas.tenant_model import PlanType
        from unittest.mock import Mock
        
        # Create mock tenant with enum
        mock_tenant = Mock()
        mock_tenant.id = 1
        mock_tenant.plan = PlanType.pro
        
        # Create mock db
        mock_db = Mock()
        mock_db.query.return_value.join.return_value.filter.return_value.scalar.return_value = 5
        
        # This should not raise an exception
        try:
            check_daily_quota(mock_tenant, "test_user", mock_db)
            print("  ✅ Quota check with enum works")
        except Exception as e:
            print(f"  ❌ Quota check failed: {e}")
            return False
        
        return True
    except Exception as e:
        print(f"❌ Quota function test failed: {e}")
        return False

def test_enum_string_conversion():
    """Test enum to string conversion logic."""
    print("\n🧪 Testing enum to string conversion...")
    
    try:
        from backend.schemas.tenant_model import PlanType
        
        # Test enum object
        plan_enum = PlanType.pro
        plan_key = plan_enum if isinstance(plan_enum, str) else plan_enum.value
        assert plan_key == "pro"
        print("  ✅ Enum to string conversion works")
        
        # Test string object (for backward compatibility)
        plan_string = "free"
        plan_key = plan_string if isinstance(plan_string, str) else plan_string.value
        assert plan_key == "free"
        print("  ✅ String passthrough works")
        
        return True
    except Exception as e:
        print(f"❌ Enum conversion test failed: {e}")
        return False

def test_enum_values_match_plan_limits():
    """Test that all enum values have corresponding PLAN_LIMITS entries."""
    print("\n🧪 Testing enum values match PLAN_LIMITS keys...")
    
    try:
        from backend.schemas.tenant_model import PlanType
        from backend.dependencies.auth import PLAN_LIMITS
        
        enum_values = {plan.value for plan in PlanType}
        plan_keys = set(PLAN_LIMITS.keys())
        
        missing_in_limits = enum_values - plan_keys
        extra_in_limits = plan_keys - enum_values
        
        if missing_in_limits:
            print(f"  ❌ Enum values missing in PLAN_LIMITS: {missing_in_limits}")
            return False
        
        if extra_in_limits:
            print(f"  ⚠️  Extra keys in PLAN_LIMITS: {extra_in_limits}")
        
        print(f"  ✅ All enum values ({enum_values}) have PLAN_LIMITS entries")
        return True
        
    except Exception as e:
        print(f"❌ Enum-PLAN_LIMITS mapping test failed: {e}")
        return False

def main():
    """Run all enum usage tests."""
    print("🚀 Starting Enum Usage Tests")
    print("=" * 50)
    
    tests = [
        test_plan_limits_access,
        test_quota_function,
        test_enum_string_conversion,
        test_enum_values_match_plan_limits,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        if test():
            passed += 1
        else:
            failed += 1
    
    print("\n" + "=" * 50)
    print(f"📊 Enum Usage Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All enum usage tests passed! No schema-related runtime errors expected.")
        return 0
    else:
        print("❌ Some enum tests failed. Runtime errors may occur.")
        return 1

if __name__ == "__main__":
    sys.exit(main())