"""Category sections (Students / Orchestral / Jazz) and the public feed."""
from ..errors import not_found
from ..validation import CATEGORIES, require_category
from . import ROUTER
from .queries import auditions_for_list, clips_list, musicians_list, posts_list
from .serializers import SECTION_LABELS

BLURBS = {
    "students": "High school & conservatory players, youth orchestras, all-state prep.",
    "orchestral": "Section seats, sub lists and principal chairs for symphonic ensembles.",
    "jazz": "Big bands, combos and jazz studies programs looking for their next voice.",
}


def _counts(conn, category):
    return {
        "musicians": conn.execute("SELECT COUNT(*) FROM users WHERE role='musician' AND category=?", (category,)).fetchone()[0],
        "auditions": conn.execute("SELECT COUNT(*) FROM auditions WHERE category=? AND status='open'", (category,)).fetchone()[0],
    }


@ROUTER.route("GET", "/api/sections")
def list_sections(ctx):
    return {"sections": [
        {"key": key, "label": SECTION_LABELS[key], "blurb": BLURBS[key], **_counts(ctx.db, key)}
        for key in CATEGORIES
    ]}


@ROUTER.route("GET", "/api/sections/<category>")
def section_detail(ctx):
    category = ctx.params["category"]
    if category not in CATEGORIES:
        raise not_found(f"There is no section called '{category}'. Try: {', '.join(CATEGORIES)}.")
    s = ctx.settings
    return {
        "section": {"key": category, "label": SECTION_LABELS[category], "blurb": BLURBS[category], **_counts(ctx.db, category)},
        "musicians": musicians_list(ctx.db, category),
        "posts": posts_list(s, ctx.db, category=category, limit=ctx.query_int("limit", 20)),
        "clips": clips_list(s, ctx.db, category=category, limit=12),
        # Audition postings need a signed-in user; signed-out callers get null.
        "auditions": auditions_for_list(ctx, category=category) if ctx.user else None,
    }


@ROUTER.route("GET", "/api/feed")
def feed(ctx):
    category = ctx.query.get("category")
    if category:
        require_category(category)
    return {"posts": posts_list(ctx.settings, ctx.db, category=category, limit=ctx.query_int("limit", 20))}
