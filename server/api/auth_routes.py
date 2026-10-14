"""Sign-in, sign-out, demo account switching."""
from .. import auth
from ..errors import bad_request, not_found, unauthorized
from ..responses import JsonResponse
from ..validation import require_text
from . import ROUTER
from .lookups import get_user
from .serializers import brief_user, own_user


def _sign_in(ctx, user):
    token = auth.create_session(ctx.db, user["id"])
    ctx.cookie_header = auth.session_cookie(token)
    return {"user": own_user(user)}


@ROUTER.route("GET", "/api/me")
def me(ctx):
    return {"user": own_user(ctx.user) if ctx.user else None}


@ROUTER.route("GET", "/api/accounts")
def accounts(ctx):
    rows = ctx.db.execute("SELECT * FROM users ORDER BY id").fetchall()
    people = [{**brief_user(r), "email": r["email"]} for r in rows]
    return {
        "musicians": [p for p in people if p["role"] == "musician"],
        "directors": [p for p in people if p["role"] == "director"],
    }


@ROUTER.route("POST", "/api/sign-in")
def sign_in(ctx):
    data = ctx.json()
    user = auth.authenticate(ctx.db, require_text(data, "email", "your email"), require_text(data, "password", "your password"))
    if not user:
        raise unauthorized("That email and password do not match. In the demo every account's password is 'demo'.")
    return _sign_in(ctx, user)


@ROUTER.route("POST", "/api/sign-in-as")
def sign_in_as_role(ctx):
    """Demo shortcut: one click into the first seed account of a role."""
    role = ctx.json().get("role")
    if role not in ("musician", "director"):
        raise bad_request("Choose a role: 'musician' or 'director'.")
    user = ctx.db.execute("SELECT * FROM users WHERE role = ? ORDER BY id LIMIT 1", (role,)).fetchone()
    if not user:
        raise not_found(f"There is no {role} account yet. Start the server with --reset to reseed.")
    return _sign_in(ctx, user)


@ROUTER.route("POST", "/api/switch")
def switch_account(ctx):
    """Demo account switcher: become any seed account without a password."""
    user_id = ctx.json().get("user_id")
    user = get_user(ctx.db, user_id) if isinstance(user_id, int) else None
    if not user:
        raise not_found("That account does not exist.")
    if ctx.user:
        auth.delete_session(ctx.db, ctx.session_token)
    return _sign_in(ctx, user)


@ROUTER.route("POST", "/api/sign-out")
def sign_out(ctx):
    token = ctx.session_token
    if token:
        auth.delete_session(ctx.db, token)
    ctx.cookie_header = auth.cleared_cookie()
    return {"ok": True}
