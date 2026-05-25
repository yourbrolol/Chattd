import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


def forwards_migrate_whitelist_and_owners(apps, schema_editor):
    ChatRoom = apps.get_model('chat', 'ChatRoom')
    RoomMembership = apps.get_model('chat', 'RoomMembership')

    for room in ChatRoom.objects.all():
        if room.owner_id is not None:
            RoomMembership.objects.get_or_create(
                room_id=room.id,
                user_id=room.owner_id,
                defaults={'role': 'owner'},
            )
        for user_id in room.whitelisted.values_list('pk', flat=True):
            membership, created = RoomMembership.objects.get_or_create(
                room_id=room.id,
                user_id=user_id,
                defaults={'role': 'member'},
            )
            if not created and membership.role != 'owner':
                membership.role = 'member'
                membership.save(update_fields=['role'])


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0005_chatroom_owner_chatroom_room_type_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='RoomMembership',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('role', models.CharField(
                    choices=[
                        ('owner', 'Owner'),
                        ('member', 'Member'),
                        ('moderator', 'Moderator'),
                        ('admin', 'Admin'),
                    ],
                    default='member',
                    max_length=20,
                )),
                ('joined_at', models.DateTimeField(auto_now_add=True)),
                ('room', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='memberships',
                    to='chat.chatroom',
                )),
                ('user', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='room_memberships',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
        ),
        migrations.AddConstraint(
            model_name='roommembership',
            constraint=models.UniqueConstraint(
                condition=models.Q(('user__isnull', False)),
                fields=('room', 'user'),
                name='unique_room_user_membership',
            ),
        ),
        migrations.AddField(
            model_name='chatroom',
            name='members',
            field=models.ManyToManyField(
                blank=True,
                related_name='member_chatrooms',
                through='chat.RoomMembership',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.RunPython(forwards_migrate_whitelist_and_owners, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name='chatroom',
            name='whitelisted',
        ),
    ]
