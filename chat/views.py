from django.http import JsonResponse
from chat.models import ChatRoom

def list_rooms(request):
    rooms = list(ChatRoom.objects.values("id", "name"))
    return JsonResponse(rooms, safe=False)