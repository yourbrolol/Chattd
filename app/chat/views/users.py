import os
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from chat.services.users import get_user_profile_data, USER_NOT_FOUND
from chat.models import User

@login_required
def user_get(request, user_id):
    data, status = get_user_profile_data(user_id)
    if status == USER_NOT_FOUND:
        return JsonResponse({"error": "not_found"}, status=404)
    return JsonResponse(data)

@login_required
def settings_edit(request):
    if request.method != 'POST':
        return JsonResponse({"error": "Method not allowed"}, status=405)

    user = request.user
    username_changed = False
    avatar_changed = False

    new_username = request.POST.get('username', '').strip()
    if new_username and new_username != user.username:
        if User.objects.filter(username=new_username).exclude(pk=user.pk).exists():
            return JsonResponse({"error": "This username is already taken."}, status=400)
        
        user.username = new_username
        username_changed = True

    avatar_file = request.FILES.get('avatar')
    if avatar_file:
        if avatar_file.size > 2 * 1024 * 1024:
            return JsonResponse({"error": "File size exceeds limit of 2MB"}, status=400)

        filename = avatar_file.name
        ext = filename.split('.')[-1].lower() if '.' in filename else ''
        if ext not in ['png', 'jpg', 'jpeg', 'gif', 'webp']:
            return JsonResponse({"error": "Invalid file format. Only PNG, JPG, JPEG, GIF, and WEBP are allowed."}, status=400)

        if user.avatar:
            try:
                old_path = user.avatar.path
                if os.path.exists(old_path):
                    os.remove(old_path)
            except Exception:
                pass

        user.avatar = avatar_file
        avatar_changed = True

    if username_changed or avatar_changed:
        user.save()
    else:
        return JsonResponse({"error": "No changes detected."}, status=400)

    response_data = {"success": True}
    if avatar_changed:
        response_data["avatar_url"] = user.avatar.url

    return JsonResponse(response_data)