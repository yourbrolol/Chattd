# make_data.py
import random
# Change 'chat' to your actual Django app folder name
from chat.models import User, ChatRoom, RoomMembership, RoomApplication, ChatMessage

def run():
    print("--> Generating concise makeshift data...")

    # 1. Create exactly 5 Users
    usernames = ["alice", "bob", "charlie", "david", "eve"]
    users = []
    for name in usernames:
        # get_or_create prevents errors if you run the script multiple times
        user, created = User.objects.get_or_create(username=name)
        if created:
            user.set_password("password123")
            user.save()
        users.append(user)

    # 2. Create 3 Rooms (one for each type)
    rooms_data = [
        {"name": "General-Public", "type": ChatRoom.RoomTypes.PUBLIC, "owner": users[0]},   # Alice's room
        {"name": "Internal-Unlisted", "type": ChatRoom.RoomTypes.UNLISTED, "owner": users[1]}, # Bob's room
        {"name": "Staff-Private", "type": ChatRoom.RoomTypes.PRIVATE, "owner": users[2]},   # Charlie's room
    ]

    rooms = []
    for r_data in rooms_data:
        room, _ = ChatRoom.objects.get_or_create(
            name=r_data["name"],
            defaults={"room_type": r_data["type"], "owner": r_data["owner"]}
        )
        rooms.append(room)
        # Ensure the owner is automatically an OWNER member
        RoomMembership.objects.get_or_create(room=room, user=r_data["owner"], defaults={"role": RoomMembership.Role.OWNER})

    # 3. Add a couple of extra members to rooms
    # Bob joins Alice's public room as a standard member
    RoomMembership.objects.get_or_create(room=rooms[0], user=users[1], defaults={"role": RoomMembership.Role.MEMBER})
    # Alice joins Bob's unlisted room as a moderator
    RoomMembership.objects.get_or_create(room=rooms[1], user=users[0], defaults={"role": RoomMembership.Role.MODERATOR})

    # 4. Create Room Applications for the Private Room
    # David and Eve apply to join Charlie's Private room
    RoomApplication.objects.get_or_create(applicant=users[3], room=rooms[2], defaults={"status": RoomApplication.Status.PENDING})
    RoomApplication.objects.get_or_create(applicant=users[4], room=rooms[2], defaults={"status": RoomApplication.Status.PENDING})

    # 5. Create basic placeholder messages
    messages = [
        {"room": rooms[0], "user": users[0], "content": "Welcome to the Public room!"},
        {"room": rooms[0], "user": users[1], "content": "Thanks Alice, happy to be here."},
        {"room": rooms[1], "user": users[1], "content": "Hey Alice, this room is unlisted so keep it low-key."},
        {"room": rooms[1], "user": users[0], "content": "Got it, I won't share the link."},
        {"room": rooms[2], "user": users[2], "content": "This is a private staff room. Waiting for access requests."},
    ]

    for msg in messages:
        ChatMessage.objects.create(
            room=msg["room"],
            user=msg["user"],
            content=msg["content"]
        )

    print(f">>> Successfully populated: 5 Users, 3 Rooms, 2 Applications, and {len(messages)} Messages!")

if __name__ == '__main__':
    run()