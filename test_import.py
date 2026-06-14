"""Test book import."""
import sys
sys.path.insert(0, r'E:\SAL o3')
from api_client import APIClient

api = APIClient("http://127.0.0.1:8000")

# Login first
login_result = api.login("admin", "admin123")
print(f"Login: {login_result.get('username')}")

# Import books
try:
    result = api.import_books(r"E:\SAL o3\test_books_5000.xlsx")
    print(f"Imported: {result.get('imported')}")
    print(f"Errors: {len(result.get('errors', []))}")
    print(f"Message: {result.get('message')}")
except Exception as e:
    print(f"Import failed: {e}")
    import traceback
    traceback.print_exc()
