from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required
def index(request):
    can_manage = request.user.is_superuser or request.user.role in {"dean", "director", "admin"}
    return render(request, "marketing/index.html", {
        "marketing_config": {
            "apiBase": "/api/v1/marketing/",
            "canManage": can_manage,
            "academyUrl": "/academy/#tools",
        },
    })
