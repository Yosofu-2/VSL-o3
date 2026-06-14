"""Quick login test."""
import httpx
r = httpx.post('http://127.0.0.1:8000/api/readers/login', json={'card_number': 'R001', 'password': 'reader123'})
print(f'Status: {r.status_code}')
print(f'Body: {r.text[:300]}')
