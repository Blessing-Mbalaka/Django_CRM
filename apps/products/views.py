from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required
def catalogue_view(request):
    return render(request, 'products/catalogue.html')

