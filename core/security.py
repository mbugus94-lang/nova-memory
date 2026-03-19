"""
Authentication, Authorization & Security
JWT tokens, RBAC, encryption, and audit logging
"""

import logging
import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any, Optional, Set
from enum import Enum
import json

try:
    import jwt
    JWT_AVAILABLE = True
except ImportError:
    JWT_AVAILABLE = False

try:
    from cryptography.fernet import Fernet
    ENCRYPTION_AVAILABLE = True
except ImportError:
    ENCRYPTION_AVAILABLE = False

logger = logging.getLogger(__name__)


class Role(str, Enum):
    """Role-based access control roles"""
    ADMIN = "admin"
    MANAGER = "manager"
    AGENT = "agent"
    VIEWER = "viewer"


class Permission(str, Enum):
    """Permissions for operations"""
    CREATE_MEMORY = "create:memory"
    READ_MEMORY = "read:memory"
    UPDATE_MEMORY = "update:memory"
    DELETE_MEMORY = "delete:memory"
    SHARE_MEMORY = "share:memory"

    CREATE_AGENT = "create:agent"
    READ_AGENT = "read:agent"
    UPDATE_AGENT = "update:agent"
    DELETE_AGENT = "delete:agent"

    MANAGE_COLLABORATION = "manage:collaboration"
    MANAGE_USERS = "manage:users"
    VIEW_AUDIT_LOG = "view:audit_log"

    ADMIN_ALL = "admin:all"


# Role to permissions mapping
ROLE_PERMISSIONS: Dict[Role, Set[Permission]] = {
    Role.ADMIN: {
        Permission.ADMIN_ALL,  # Admins have all permissions
        Permission.VIEW_AUDIT_LOG,
        Permission.MANAGE_USERS,
    },
    Role.MANAGER: {
        Permission.CREATE_MEMORY,
        Permission.READ_MEMORY,
        Permission.UPDATE_MEMORY,
        Permission.DELETE_MEMORY,
        Permission.SHARE_MEMORY,
        Permission.CREATE_AGENT,
        Permission.READ_AGENT,
        Permission.UPDATE_AGENT,
        Permission.MANAGE_COLLABORATION,
        Permission.VIEW_AUDIT_LOG,
    },
    Role.AGENT: {
        Permission.CREATE_MEMORY,
        Permission.READ_MEMORY,
        Permission.UPDATE_MEMORY,
        Permission.SHARE_MEMORY,
        Permission.READ_AGENT,
    },
    Role.VIEWER: {
        Permission.READ_MEMORY,
        Permission.READ_AGENT,
    },
}


class JWTManager:
    """JWT token management"""

    def __init__(
        self,
        secret_key: str = None,
        algorithm: str = "HS256",
        expiration_hours: int = 24,
    ):
        """
        Initialize JWT manager

        Args:
            secret_key: Secret key for signing tokens
            algorithm: JWT algorithm to use
            expiration_hours: Token expiration time in hours
        """
        if not JWT_AVAILABLE:
            logger.warning("JWT not available - install PyJWT")
            self.available = False
            return

        self.available = True
        self.secret_key = secret_key or secrets.token_urlsafe(32)
        self.algorithm = algorithm
        self.expiration_hours = expiration_hours

    def create_token(
        self,
        agent_id: str,
        role: Role = Role.AGENT,
        permissions: List[Permission] = None,
        extra_claims: Dict[str, Any] = None,
    ) -> Optional[str]:
        """Create a JWT token for an agent"""
        if not self.available:
            return None

        try:
            now = datetime.now(timezone.utc)
            expiration = now + timedelta(hours=self.expiration_hours)

            payload = {
                "agent_id": agent_id,
                "role": role.value,
                "permissions": [p.value for p in (permissions or ROLE_PERMISSIONS[role])],
                "iat": now,
                "exp": expiration,
            }

            if extra_claims:
                payload.update(extra_claims)

            token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
            logger.info(f"Token created for agent: {agent_id}")
            return token
        except Exception as e:
            logger.error(f"Error creating token: {e}")
            return None

    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode a JWT token"""
        if not self.available:
            return None

        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("Token expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            return None

    def has_permission(
        self,
        token: str,
        required_permission: Permission,
    ) -> bool:
        """Check if token holder has a specific permission"""
        payload = self.verify_token(token)
        if not payload:
            return False

        permissions = payload.get("permissions", [])
        Role(payload.get("role", Role.VIEWER.value))

        # Check for admin all permission
        if "admin:all" in permissions:
            return True

        # Check specific permission
        return required_permission.value in permissions


class AttributeManager:
    """Manage attribute-based access control"""

    def __init__(self):
        """Initialize attribute manager"""
        # Map of (agent_id, resource_id) -> attributes
        self.attributes: Dict[tuple, Dict[str, Any]] = {}

    def set_attributes(
        self,
        agent_id: str,
        resource_id: str,
        attributes: Dict[str, Any],
    ) -> None:
        """Set attributes for an agent-resource pair"""
        key = (agent_id, resource_id)
        self.attributes[key] = attributes
        logger.debug(f"Attributes set for {agent_id}:{resource_id}")

    def get_attributes(
        self,
        agent_id: str,
        resource_id: str,
    ) -> Dict[str, Any]:
        """Get attributes for an agent-resource pair"""
        key = (agent_id, resource_id)
        return self.attributes.get(key, {})

    def can_access(
        self,
        agent_id: str,
        resource_id: str,
        required_attributes: Dict[str, Any],
    ) -> bool:
        """Check if agent can access resource based on attributes"""
        attributes = self.get_attributes(agent_id, resource_id)

        for key, required_value in required_attributes.items():
            if attributes.get(key) != required_value:
                return False

        return True


class EncryptionManager:
    """Manage encryption of sensitive memory data"""

    def __init__(self, key: str = None):
        """
        Initialize encryption manager

        Args:
            key: Encryption key (base64 encoded)
        """
        if not ENCRYPTION_AVAILABLE:
            logger.warning("Encryption not available - install cryptography")
            self.available = False
            return

        self.available = True
        if key:
            self.cipher = Fernet(key.encode() if isinstance(key, str) else key)
        else:
            # Generate new key
            self.encryption_key = Fernet.generate_key()
            self.cipher = Fernet(self.encryption_key)
            logger.info("Generated new encryption key")

    def encrypt(self, plaintext: str) -> Optional[str]:
        """Encrypt plaintext"""
        if not self.available:
            return plaintext

        try:
            ciphertext = self.cipher.encrypt(plaintext.encode())
            return ciphertext.decode()
        except Exception as e:
            logger.error(f"Encryption error: {e}")
            return plaintext

    def decrypt(self, ciphertext: str) -> Optional[str]:
        """Decrypt ciphertext"""
        if not self.available:
            return ciphertext

        try:
            plaintext = self.cipher.decrypt(ciphertext.encode())
            return plaintext.decode()
        except Exception as e:
            logger.error(f"Decryption error: {e}")
            return ciphertext


class AuditLog:
    """Audit logging for security and compliance"""

    def __init__(self, max_entries: int = 10000):
        """
        Initialize audit log

        Args:
            max_entries: Maximum number of entries to keep
        """
        self.entries: List[Dict[str, Any]] = []
        self.max_entries = max_entries

    def log(
        self,
        action: str,
        actor: str,
        resource: str,
        status: str = "success",
        details: Dict[str, Any] = None,
    ) -> None:
        """Log an action"""
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "action": action,
            "actor": actor,
            "resource": resource,
            "status": status,
            "details": details or {},
        }

        self.entries.append(entry)

        # Keep log size bounded
        if len(self.entries) > self.max_entries:
            self.entries.pop(0)

        logger.info(f"Audit: {actor} {action} {resource} ({status})")

    def get_logs(
        self,
        actor: str = None,
        action: str = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get audit logs with optional filtering"""
        filtered = self.entries

        if actor:
            filtered = [e for e in filtered if e["actor"] == actor]

        if action:
            filtered = [e for e in filtered if e["action"] == action]

        return filtered[-limit:]

    def export(self) -> str:
        """Export audit log as JSON"""
        return json.dumps(self.entries, indent=2)


# Global instances
_jwt_manager: Optional[JWTManager] = None
_encryption_manager: Optional[EncryptionManager] = None
_audit_log: Optional[AuditLog] = None
_attribute_manager: Optional[AttributeManager] = None


def get_jwt_manager() -> JWTManager:
    """Get or create JWT manager"""
    global _jwt_manager
    if _jwt_manager is None:
        _jwt_manager = JWTManager()
    return _jwt_manager


def get_encryption_manager() -> EncryptionManager:
    """Get or create encryption manager"""
    global _encryption_manager
    if _encryption_manager is None:
        _encryption_manager = EncryptionManager()
    return _encryption_manager


def get_audit_log() -> AuditLog:
    """Get or create audit log"""
    global _audit_log
    if _audit_log is None:
        _audit_log = AuditLog()
    return _audit_log


def get_attribute_manager() -> AttributeManager:
    """Get or create attribute manager"""
    global _attribute_manager
    if _attribute_manager is None:
        _attribute_manager = AttributeManager()
    return _attribute_manager


def hash_password(password: str, salt: str = None) -> tuple[str, str]:
    """Hash a password with salt"""
    if salt is None:
        salt = secrets.token_hex(16)

    hash_obj = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode(),
        salt.encode(),
        100000,
    )

    return hash_obj.hex(), salt


def verify_password(password: str, hash_value: str, salt: str) -> bool:
    """Verify a password against its hash"""
    computed_hash, _ = hash_password(password, salt)
    return computed_hash == hash_value
