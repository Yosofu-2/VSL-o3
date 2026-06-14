"""Test password verification."""
from app.models.model import verify_password

# Test with the stored hash
stored_hash = "a9df047df12543bb9eb50e65d523f54b:511f4ef1d3ca0abda3af82a931a56d238142a0e83303f628cc03a9d2eae2b0c2"
test_password = "reader123"

try:
    result = verify_password(test_password, stored_hash)
    print(f'Verification result: {result}')
except Exception as e:
    print(f'Error: {type(e).__name__}: {e}')
    import traceback
    traceback.print_exc()
