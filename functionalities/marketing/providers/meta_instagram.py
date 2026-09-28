from django.conf import settings

from .base import ProviderError, ProviderResult
from .meta_common import is_public_https_url, post_graph


def create_instagram_container(message):
    media_url = getattr(message, "media_url_snapshot", "")
    if not is_public_https_url(media_url):
        raise ProviderError("Instagram requires a publicly reachable HTTPS image URL.", retryable=False)
    data = post_graph(
        f"{settings.META_INSTAGRAM_USER_ID}/media",
        token=settings.META_INSTAGRAM_ACCESS_TOKEN,
        payload={"image_url": media_url, "caption": message.content_snapshot},
    )
    provider_id = data.get("id", "")
    if not provider_id:
        raise ProviderError("Meta did not return an Instagram container identifier.", retryable=True)
    return ProviderResult(str(provider_id), "accepted", {"phase": "container"}, retryable=False)


def publish_instagram_media(container_id):
    if not container_id:
        raise ProviderError("Instagram container identifier is required.", retryable=False)
    data = post_graph(
        f"{settings.META_INSTAGRAM_USER_ID}/media_publish",
        token=settings.META_INSTAGRAM_ACCESS_TOKEN,
        payload={"creation_id": container_id},
    )
    provider_id = data.get("id", "")
    if not provider_id:
        raise ProviderError("Meta did not return an Instagram media identifier.", retryable=True)
    return ProviderResult(str(provider_id), "accepted", {"phase": "published"}, retryable=False)


def publish_instagram_post(message):
    container = create_instagram_container(message)
    return publish_instagram_media(container.provider_id)
