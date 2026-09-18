import re
from urllib.parse import parse_qs, urlparse

from django.core.exceptions import ValidationError


YOUTUBE_VIDEO_ID_PATTERN = re.compile(r'^[A-Za-z0-9_-]{11}$')
YOUTUBE_HOSTS = {
    'youtube.com',
    'www.youtube.com',
    'm.youtube.com',
    'youtu.be',
    'www.youtu.be',
    'youtube-nocookie.com',
    'www.youtube-nocookie.com',
}


def extract_youtube_video_id(url: str) -> str:
    """Return a video ID from an allowlisted YouTube URL."""
    parsed = urlparse((url or '').strip())
    host = (parsed.hostname or '').lower()
    if parsed.scheme != 'https' or host not in YOUTUBE_HOSTS:
        raise ValidationError('Enter a supported YouTube URL using HTTPS.')

    path_parts = [part for part in parsed.path.split('/') if part]
    if host in {'youtu.be', 'www.youtu.be'}:
        video_id = path_parts[0] if path_parts else ''
    elif parsed.path == '/watch':
        video_id = parse_qs(parsed.query).get('v', [''])[0]
    elif len(path_parts) >= 2 and path_parts[0] in {'embed', 'shorts', 'live'}:
        video_id = path_parts[1]
    else:
        video_id = ''

    if not YOUTUBE_VIDEO_ID_PATTERN.fullmatch(video_id):
        raise ValidationError('Enter a URL containing a valid YouTube video ID.')
    return video_id

