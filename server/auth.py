"""Password hashing, cookie sessions and the guards API modules use."""
import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone

from .config import SESSION_COOKIE, SESSION_DAYS, log
from .errors import forbidden, unauthorized

_ITERATIONS = 100_000


def hash_password(password: str, salt: str = None) -> str:
    salt = salt or secrets.token_hex(8)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), _ITERATIONS).hex()
    return f"{salt}${digest}"


def verify_password(password: str, stored: str) -> bool:
    salt, _, _ = stored.partition("$")
    return hmac.compare_digest(hash_password(password, salt), stored)


def _stamp(moment: datetime) -> str:
    return moment.strftime("%Y-%m-%dT%H:%M:%SZ")


def create_session(conn, user_id: int) -> str:
    token = secrets.token_urlsafe(32)
    expires = _stamp(datetime.now(timezone.utc) + timedelta(days=SESSION_DAYS))
    conn.execute("INSERT INTO sessions (token, user_id, expires) VALUES (?,?,?)", (token, user_id, expires))
    conn.commit()
    return token


def delete_session(conn, token: str) -> None:
    conn.execute("DELETE FROM sessions WHERE token = ?", (token,))
    conn.commit()


def user_for_token(conn, token: str):
    """The signed-in user row for a session token, or None."""
    if not token:
        return None
    row = conn.execute(
        "SELECT u.* FROM sessions s JOIN users u ON u.id = s.user_id WHERE s.token = ? AND s.expires > ?",
        (token, _stamp(datetime.now(timezone.utc))),
    ).fetchone()
    return row


def authenticate(conn, email: str, password: str):
    user = conn.execute("SELECT * FROM users WHERE lower(email) = lower(?)", (email.strip(),)).fetchone()
    if user and verify_password(password, user["password_hash"]):
        return user
    log.info("Failed sign-in for %s", email)
    return None


def require_user(ctx):
    if not ctx.user:
        raise unauthorized("Please sign in to do that.")
    return ctx.user


def require_role(ctx, role: str, action: str):
    user = require_user(ctx)
    if user["role"] != role:
        raise forbidden(f"Only {role}s can {action}. You are signed in as a {user['role']}.")
    return user


def session_cookie(token: str) -> str:
    return f"{SESSION_COOKIE}={token}; Path=/; HttpOnly; SameSite=Lax; Max-Age={SESSION_DAYS * 86400}"


def cleared_cookie() -> str:
    return f"{SESSION_COOKIE}=; Path=/; HttpOnly; SameSite=Lax; Max-Age=0"
