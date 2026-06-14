"""Test reader login and capture full error."""
import httpx, json

r = httpx.post('http://127.0.0.1:8000/api/readers/login', json={
    'card_number': 'R001',
    'password': 'reader123'
})
print(f'Status: {r.status_code}')
print(f'Headers: {dict(r.headers)}')
print(f'Body: {r.text}')
