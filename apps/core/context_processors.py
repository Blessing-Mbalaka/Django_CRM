from functionalities.crm_core.navigation import get_suite_navigation


def suite_navigation(request):
    if not request.user.is_authenticated:
        return {'suite_navigation': []}
    return {'suite_navigation': get_suite_navigation(request.user)}
