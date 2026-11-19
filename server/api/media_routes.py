"""Public video files: seed clips (my-clips/) and uploaded profile clips."""
from ..errors import not_found
from ..media import safe_child
from ..responses import FileResponse
from . import ROUTER
from ..auth import require_user
from ..errors import forbidden


def protect_blind_source(ctx, path):
    """Authorize the actual file, including case, Unicode, symlink and hardlink aliases."""
    target = path.stat()
    directories = {"library": ctx.settings.clips_dir, "upload": ctx.settings.profile_uploads_dir}
    clips = ctx.db.execute(
        "SELECT DISTINCT c.owner_id, c.source, c.file FROM clips c JOIN submissions s ON s.clip_id=c.id "
        "JOIN auditions a ON a.id=s.audition_id WHERE a.blind_review=1"
    ).fetchall()
    owners = set()
    for clip in clips:
        directory = directories.get(clip["source"])
        original = safe_child(directory, clip["file"]) if directory else None
        if original:
            identity = original.stat()
            if (identity.st_dev, identity.st_ino) == (target.st_dev, target.st_ino):
                owners.add(clip["owner_id"])
    if owners:
        user = require_user(ctx)
        if user["role"] != "musician" or owners != {user["id"]}:
            raise forbidden("This recording is used in a blind application. Reviewers must use the scoped audio player.")


@ROUTER.route("GET", "/media/clips/<name>")
def library_clip(ctx):
    path = safe_child(ctx.settings.clips_dir, ctx.params["name"])
    if not path:
        raise not_found("This clip is coming soon: no video file is in my-clips/ yet.")
    protect_blind_source(ctx, path)
    return FileResponse(path)


@ROUTER.route("GET", "/media/uploads/<name>")
def uploaded_profile_clip(ctx):
    path = safe_child(ctx.settings.profile_uploads_dir, ctx.params["name"])
    if not path:
        raise not_found("That clip file was not found.")
    protect_blind_source(ctx, path)
    return FileResponse(path)
