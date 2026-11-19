"""Fictional preview catalogue; deliberately has no submission or registration endpoints."""
from ..auth import require_user
from ..demo_discovery import previews
from ..discovery import GENRES
from . import ROUTER


@ROUTER.route("GET", "/api/discovery")
def discovery_catalogue(ctx):
    require_user(ctx)
    return {"previews": previews(ctx.db), "genres": GENRES}
