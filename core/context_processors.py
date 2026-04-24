from django.conf import settings

def ui(request):
    user = getattr(request, "user", None)
    group_name = getattr(settings, "TECHNICIANS_GROUP_NAME", "Tecnicos")
    is_tech = False
    if user and user.is_authenticated:
        is_tech = bool(user.is_superuser or user.groups.filter(name=group_name).exists())
    return {
        "IS_TECHNICIAN": is_tech,
        "TECHNICIANS_GROUP_NAME": group_name,
    }
