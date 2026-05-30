from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from chat.services.users import get_user_profile_data, USER_NOT_FOUND

@login_required
def user_get(request, user_id):
    data, status = get_user_profile_data(user_id)
    if status == USER_NOT_FOUND:
        return JsonResponse({"error": "not_found"}, status=404)
    return JsonResponse(data)