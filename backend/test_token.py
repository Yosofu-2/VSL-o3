"""Test create_access_token directly."""
from app.security import create_access_token

try:
    token = create_access_token(data={
        "sub": "1",
        "card_number": "R001",
        "role": "reader",
        "type": "reader"
    })
    print(f'Token created: {token[:50]}...')
except Exception as e:
    print(f'Error: {type(e).__name__}: {e}')
