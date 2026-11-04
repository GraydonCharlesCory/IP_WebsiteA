"""Public video files: seed clips (my-clips/) and uploaded profile clips."""
from ..errors import not_found
from ..media import safe_child
from ..responses import FileResponse
from . import ROUTER


@ROUTER.route("GET", "/media/clips/<name>")
def library_clip(ctx):
    path = safe_child(ctx.settings.clips_dir, ctx.params["name"])
    if not path:
        raise not_found("This clip is coming soon: no video file is in my-clips/ yet.")
    return FileResponse(path)


@ROUTER.route("GET", "/media/uploads/<name>")
def uploaded_profile_clip(ctx):
    path = safe_child(ctx.settings.profile_uploads_dir, ctx.params["name"])
    if not path:
        raise not_found("That clip file was not found.")
    return FileResponse(path)
