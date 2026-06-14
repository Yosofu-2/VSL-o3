"""Test reader login after fix."""
import httpx, json

r = httpx.post('http://127.0.0.1:8000/api/readers/login', json={
    'card_number': 'R001',
    'password': 'reader123'
})
print(f'Status: {r.status_code}')
if r.status_code == 200:
    data = r.json()
    print(f'Token: {data.get("token", "N/A")[:50]}...')
    print(f'Name: {data.get("name")}')
    print(f'ID: {data.get("id")}')
else:
    print(f'Error: {r.text}')
