import os
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Union

from cryptography.fernet import Fernet
from dotenv import load_dotenv
from jose import JWTError, jwt
from passlib.context import CryptContext

from .logging_config import get_logger

# Load environment variables from backend/.env
env_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path=env_path)

logger = get_logger("auth")

# Security configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here-change-this-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Encryption key for Gibney credentials
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")
if not ENCRYPTION_KEY:
    ENCRYPTION_KEY = Fernet.generate_key()
    logger.warning(
        "Generated new encryption key - set ENCRYPTION_KEY in .env file for production"
    )
    logger.debug(f"Generated encryption key: {ENCRYPTION_KEY.decode()}")

try:
    fernet = Fernet(
        ENCRYPTION_KEY if isinstance(ENCRYPTION_KEY, bytes) else ENCRYPTION_KEY.encode()
    )
    logger.info("Encryption service initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize encryption service: {e}")
    raise

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
logger.info("Password hashing context initialized")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    logger.debug("Verifying password")
    try:
        result = pwd_context.verify(plain_password, hashed_password)
        if result:
            logger.debug("Password verification successful")
        else:
            logger.debug("Password verification failed")
        return result
    except Exception as e:
        logger.error(f"Password verification error: {e}")
        return False


def get_password_hash(password: str) -> str:
    """Hash a password"""
    logger.debug("Hashing password")
    try:
        hashed = pwd_context.hash(password)
        logger.debug("Password hashed successfully")
        return hashed
    except Exception as e:
        logger.error(f"Password hashing error: {e}")
        raise


# Alias for test compatibility
def hash_password(password: str) -> str:
    """Hash a password (alias for get_password_hash)"""
    return get_password_hash(password)


def encrypt_credential(credential: str) -> str:
    """Encrypt a credential for secure storage"""
    logger.debug("Encrypting credential")
    try:
        encrypted = fernet.encrypt(credential.encode()).decode()
        logger.debug("Credential encrypted successfully")
        return encrypted
    except Exception as e:
        logger.error(f"Credential encryption error: {e}")
        raise


def decrypt_credential(encrypted_credential: str) -> str:
    """Decrypt a credential"""
    logger.debug("Decrypting credential")
    try:
        decrypted = fernet.decrypt(encrypted_credential.encode()).decode()
        logger.debug("Credential decrypted successfully")
        return decrypted
    except Exception as e:
        logger.error(f"Credential decryption error: {e}")
        raise


def create_access_token(
    data: Union[str, Dict[str, Any]], expires_delta: Optional[timedelta] = None
) -> str:
    """Create a JWT access token"""
    logger.debug("Creating access token")

    try:
        # Handle both old format (user_id string) and new format (dict)
        if isinstance(data, str):
            to_encode: Dict[str, Any] = {"sub": data}
            logger.debug(f"Creating token for user: {data}")
        else:
            to_encode = data.copy()
            user_email = to_encode.get("sub", "unknown")
            logger.debug(f"Creating token for user: {user_email}")

        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

        logger.info(f"Access token created successfully, expires at: {expire}")
        return encoded_jwt

    except Exception as e:
        logger.error(f"Token creation error: {e}")
        raise


def verify_token(token: str) -> Optional[str]:
    """Verify a JWT token and return the user email"""
    logger.debug("Verifying JWT token")

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")

        if email is None:
            logger.warning("Token verification failed: No subject in token")
            return None

        # Check token expiration - use UTC timestamps consistently
        exp = payload.get("exp")
        if exp:
            exp_datetime = datetime.utcfromtimestamp(exp)
            current_time = datetime.utcnow()
            if current_time > exp_datetime:
                logger.warning(
                    f"Token verification failed: Token expired at {exp_datetime} UTC (current time: {current_time} UTC)"
                )
                return None

        logger.debug(f"Token verified successfully for user: {email}")
        return str(email)

    except JWTError as e:
        logger.warning(f"JWT verification failed: {e}")
        return None
    except Exception as e:
        logger.error(f"Token verification error: {e}")
        return None
