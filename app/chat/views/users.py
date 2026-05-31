import os
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from chat.services.users import get_user_profile_data, USER_NOT_FOUND

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

    avatar_file = request.FILES.get('avatar')
    if not avatar_file:
        return JsonResponse({"error": "No avatar file provided"}, status=400)

    # Validate size (under 2MB)
    if avatar_file.size > 2 * 1024 * 1024:
        return JsonResponse({"error": "File size exceeds limit of 2MB"}, status=400)

    # Validate extension
    filename = avatar_file.name
    ext = filename.split('.')[-1].lower() if '.' in filename else ''
    if ext not in ['png', 'jpg', 'jpeg', 'gif', 'webp']:
        return JsonResponse({"error": "Invalid file format. Only PNG, JPG, JPEG, GIF, and WEBP are allowed."}, status=400)

    user = request.user

    # Remove old avatar file if it exists
    if user.avatar:
        try:
            old_path = user.avatar.path
            if os.path.exists(old_path):
                os.remove(old_path)
        except Exception as e:
            # Log error but don't block upload
            pass

    user.avatar = avatar_file
    user.save()

    return JsonResponse({
        "success": True,
        "avatar_url": user.avatar.url
    })