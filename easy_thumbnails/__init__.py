"""
TODO:
1) mongoengine doesn't support access by 'related_name'. So that,
    it needs to replace 'thumbnails' (used in Thumbnail model)
    and 'dimensions' on ThumbnailDimensions.

2) Removed model ThumbnailDimensions. Find and fix all side effects.
"""
VERSION = (2, 2, 1, 'final', 0)


def get_version(*args, **kwargs):
    # Don't litter django/__init__.py with all the get_version stuff.
    # Only import if it's actually called.
    from .get_version import get_version
    return get_version(*args, **kwargs)
