from django.conf import settings

from .base import ProviderError, ProviderResult
from .meta_common import post_graph


def publish_facebook_post(message):
    if not message.content_snapshot:
        raise ProviderError("Facebook post content is required.", retryable=False)
    payload = {"message": message.content_snapshot}
    if getattr(message, "media_url_snapshot", ""):
        payload["link"] = message.media_url_snapshot
    data = post_graph(
        f"{settings.META_FACEBOOK_PAGE_ID}/feed",
        token=settings.META_FACEBOOK_PAGE_ACCESS_TOKEN,
        payload=payload,
    )
    provider_id = data.get("id", "")
    if not provider_id:
        raise ProviderError("Meta did not return a Facebook post identifier.", retryable=True)
    return ProviderResult(str(provider_id), "accepted", {"channel": "facebook"}, retryable=False)
