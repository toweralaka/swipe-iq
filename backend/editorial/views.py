from django.contrib.admin.views.decorators import staff_member_required
from django.core.exceptions import PermissionDenied
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from .models import MediaAsset


@staff_member_required
def media_preview(request, asset_id):
    if not request.user.has_perm("editorial.view_mediaasset"):
        raise PermissionDenied
    asset = get_object_or_404(MediaAsset, pk=asset_id)
    response = FileResponse(asset.file.open("rb"))
    response["Cache-Control"] = "private, no-store"
    response["X-Content-Type-Options"] = "nosniff"
    return response
