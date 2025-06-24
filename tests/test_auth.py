import pytest
from datetime import timedelta
from app.auth import hash_password, verify_password, create_access_token, verify_token


@pytest.mark.unit
class TestPasswordHashing:
    """Test password hashing and verification"""
    
    def test_hash_password(self):
        """Test password hashing"""
        password = "testpassword123"
        hashed = hash_password(password)
        
        assert hashed != password
        assert len(hashed) > 0
        assert hashed.startswith("$2b$")
    
    def test_verify_password_correct(self):
        """Test password verification with correct password"""
        password = "testpassword123"
        hashed = hash_password(password)
        
        assert verify_password(password, hashed) is True
    
    def test_verify_password_incorrect(self):
        """Test password verification with incorrect password"""
        password = "testpassword123"
        wrong_password = "wrongpassword"
        hashed = hash_password(password)
        
        assert verify_password(wrong_password, hashed) is False
    
    def test_different_passwords_different_hashes(self):
        """Test that different passwords produce different hashes"""
        password1 = "password1"
        password2 = "password2"
        
        hash1 = hash_password(password1)
        hash2 = hash_password(password2)
        
        assert hash1 != hash2


@pytest.mark.unit
class TestJWTTokens:
    """Test JWT token creation and verification"""
    
    def test_create_access_token(self):
        """Test JWT token creation"""
        user_id = "test-user-id"
        token = create_access_token(user_id)
        
        assert isinstance(token, str)
        assert len(token) > 0
        assert "." in token  # JWT tokens have dots
    
    def test_create_access_token_with_expiry(self):
        """Test JWT token creation with custom expiry"""
        user_id = "test-user-id"
        expires_delta = timedelta(minutes=30)
        token = create_access_token(user_id, expires_delta)
        
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_verify_token_valid(self):
        """Test token verification with valid token"""
        user_id = "test-user-id"
        token = create_access_token(user_id)
        
        payload = verify_token(token)
        assert payload["sub"] == user_id
        assert "exp" in payload
    
    def test_verify_token_invalid(self):
        """Test token verification with invalid token"""
        invalid_token = "invalid.token.here"
        
        payload = verify_token(invalid_token)
        assert payload is None
    
    def test_verify_token_expired(self):
        """Test token verification with expired token"""
        user_id = "test-user-id"
        expires_delta = timedelta(seconds=-1)  # Already expired
        token = create_access_token(user_id, expires_delta)
        
        payload = verify_token(token)
        assert payload is None 