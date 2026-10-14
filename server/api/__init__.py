"""All API routes register themselves on ROUTER when their module is imported."""
from ..router import Router

ROUTER = Router()

from . import (  # noqa: E402,F401  (imports register the routes)
    auth_routes, media_routes, sections, musicians, posts_clips, auditions, submissions, reviews, director,
)
