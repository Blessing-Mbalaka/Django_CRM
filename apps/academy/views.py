from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.urls import reverse


@login_required
def academy_index(request):
    response = render(request, 'academy/index.html', {
        'academy_paths_url': reverse('academy-path-list'),
        'academy_courses_url': reverse('academy-course-list'),
    })
    response.headers['Content-Security-Policy'] = (
        'frame-src https://www.youtube.com https://www.youtube-nocookie.com'
    )
    return response

