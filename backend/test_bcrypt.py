"""Direct test of password hash and verify with new bcrypt code."""
from app.security import hash_password, verify_password

# Test new hash
h = hash_password("reader123")
print(f"New hash: {h}")
print(f"Verify: {verify_password('reader123', h)}")

# Test old SHA256 hash
old_hash = "a9df047df12543bb9eb50e65d523f54b:511f4ef1d3ca0abda3af82a931a56d238142a0e83303f628cc03a9d2eae2b0c2"
print(f"Old hash verify: {verify_password('reader123', old_hash)}")
