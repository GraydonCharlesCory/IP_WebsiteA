"""All API routes register themselves on ROUTER when their module is imported."""
from ..router import Router

ROUTER = Router()

from . import (  # noqa: E402,F401  (imports register the routes)
    auth_routes, media_routes, sections, musicians, teachers, posts_clips, ensembles, opportunities, gigs, submissions,
    submission_workflow, applications, reviews, credibility, director, judging, notifications, schools, discovery,
)
