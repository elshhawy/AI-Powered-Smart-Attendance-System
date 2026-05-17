# scripts/test_auth.py
# Run from the project root: python scripts/test_auth.py
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.security import (
    hash_password, verify_password,
    create_access_token, create_refresh_token, verify_token
)
from jose import JWTError

def run():
    print("=" * 50)
    print("Phase 2 Auth Tests")
    print("=" * 50)

    # ── Test 1: Password hashing ──────────────────────────────────────────
    print("\n[1] Password hashing...")
    hashed = hash_password("mysecretpassword")
    assert hashed != "mysecretpassword", "Hash must not equal plain text"
    assert hashed.startswith("$2b$"), "Must be a bcrypt hash"
    # Same password hashed twice gives DIFFERENT results (random salt)
    assert hash_password("mysecretpassword") != hashed, \
        "Each hash should be unique (random salt)"
    print("    ✓ Password hashed correctly (bcrypt, unique salt)")

    # ── Test 2: Password verification ─────────────────────────────────────
    print("\n[2] Password verification...")
    assert verify_password("mysecretpassword", hashed) == True
    assert verify_password("wrongpassword",    hashed) == False
    assert verify_password("",                 hashed) == False
    print("    ✓ Correct password accepted, wrong password rejected")

    # ── Test 3: Access token creation and verification ────────────────────
    print("\n[3] Access token...")
    token   = create_access_token(admin_id=1)
    payload = verify_token(token, "access")
    assert payload["sub"]  == "1"
    assert payload["type"] == "access"
    print(f"    ✓ Token created and verified. Admin id: {payload['sub']}")

    # ── Test 4: Refresh token creation and verification ───────────────────
    print("\n[4] Refresh token...")
    rtoken   = create_refresh_token(admin_id=1)
    rpayload = verify_token(rtoken, "refresh")
    assert rpayload["sub"]  == "1"
    assert rpayload["type"] == "refresh"
    print("    ✓ Refresh token created and verified")

    # ── Test 5: Wrong token type is rejected ──────────────────────────────
    print("\n[5] Token type enforcement...")
    try:
        # Using a refresh token where an access token is expected
        verify_token(rtoken, "access")
        assert False, "Should have raised JWTError"
    except JWTError:
        print("    ✓ Refresh token correctly rejected as access token")

    try:
        # Using an access token where a refresh token is expected
        verify_token(token, "refresh")
        assert False, "Should have raised JWTError"
    except JWTError:
        print("    ✓ Access token correctly rejected as refresh token")

    # ── Test 6: Tampered token is rejected ────────────────────────────────
    print("\n[6] Tampered token rejection...")
    tampered = token[:-5] + "XXXXX"
    try:
        verify_token(tampered, "access")
        assert False, "Should have raised JWTError"
    except JWTError:
        print("    ✓ Tampered token correctly rejected")

    # ── Test 7: Live login test via the actual endpoint ───────────────────
    print("\n[7] Live endpoint test (server must be running on port 8000)...")
    try:
        import requests

        # Wrong password should return 401
        r = requests.post("http://localhost:8000/api/v1/auth/login",
                          json={"email": "admin@university.edu",
                                "password": "wrongpassword"},
                          timeout=3)
        assert r.status_code == 401, f"Expected 401, got {r.status_code}"
        print("    ✓ Wrong password returns 401")

        # Accessing /me without a token returns 401
        r = requests.get("http://localhost:8000/api/v1/auth/me", timeout=3)
        assert r.status_code == 401
        print("    ✓ /me without token returns 401")

        # Correct login returns 200 with tokens
        r = requests.post("http://localhost:8000/api/v1/auth/login",
                          json={"email": "admin@tanta.edu",
                                "password": "1234"},  # change this
                          timeout=3)
        if r.status_code == 200:
            data = r.json()
            assert "access_token"  in data
            assert "refresh_token" in data
            assert "admin_name"    in data
            print(f"    ✓ Login successful. Welcome, {data['admin_name']}")

            # Use the token to access /me
            headers = {"Authorization": f"Bearer {data['access_token']}"}
            r2 = requests.get("http://localhost:8000/api/v1/auth/me",
                              headers=headers, timeout=3)
            assert r2.status_code == 200
            print(f"    ✓ /me with valid token returns admin info")
        else:
            print(f"    ⚠  Login returned {r.status_code} — "
                  f"check your email/password in this test file")

    except requests.exceptions.ConnectionError:
        print("    ⚠  Server not running — skipping live tests")
        print("       Start it with: uvicorn src.main:app --reload --port 8000")

    print("\n" + "=" * 50)
    print("✅ All logic tests passed!")
    print("=" * 50)

if __name__ == "__main__":
    run()