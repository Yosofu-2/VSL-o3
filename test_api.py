"""Test API client login."""
import sys
sys.path.insert(0, r'E:\SAL o3')
from api_client import APIClient

api = APIClient("http://127.0.0.1:8000")

# Test admin login
try:
    result = api.login("admin", "admin123")
    print(f"Admin login OK: {result}")
except Exception as e:
    print(f"Admin login FAILED: {type(e).__name__}: {e}")

# Test reader login
try:
    result = api.reader_login("R001", "reader123")
    print(f"Reader login OK: {result}")
except Exception as e:
    print(f"Reader login FAILED: {type(e).__name__}: {e}")
