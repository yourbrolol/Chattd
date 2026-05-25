# Fix legacy FK: chat_chatmessage.user_id referenced accounts_user instead of chat_user.

from django.db import migrations, connection


def _table_exists(cursor, name):
    cursor.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=%s",
        [name],
    )
    return cursor.fetchone() is not None


def forwards_fix_chatmessage_user_fk(apps, schema_editor):
    if connection.vendor != 'sqlite':
        return

    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name='chat_chatmessage'"
        )
        row = cursor.fetchone()
        if not row or 'accounts_user' not in (row[0] or ''):
            return

        cursor.execute('PRAGMA foreign_keys=OFF')

        cursor.execute(
            '''
            CREATE TABLE "chat_chatmessage_new" (
                "id" integer NOT NULL PRIMARY KEY AUTOINCREMENT,
                "content" text NOT NULL,
                "timestamp" time NOT NULL,
                "user_id" bigint NULL REFERENCES "chat_user" ("id")
                    DEFERRABLE INITIALLY DEFERRED,
                "room_id" bigint NOT NULL REFERENCES "chat_chatroom" ("id")
                    DEFERRABLE INITIALLY DEFERRED
            )
            '''
        )

        if _table_exists(cursor, 'accounts_user'):
            cursor.execute(
                '''
                INSERT INTO "chat_chatmessage_new" ("id", "content", "timestamp", "room_id", "user_id")
                SELECT m."id", m."content", m."timestamp", m."room_id", cu."id"
                FROM "chat_chatmessage" m
                LEFT JOIN "accounts_user" au ON au."id" = m."user_id"
                LEFT JOIN "chat_user" cu ON cu."username" = au."username"
                '''
            )
        else:
            cursor.execute(
                '''
                INSERT INTO "chat_chatmessage_new" ("id", "content", "timestamp", "room_id", "user_id")
                SELECT "id", "content", "timestamp", "room_id", NULL
                FROM "chat_chatmessage"
                '''
            )

        cursor.execute('DROP TABLE "chat_chatmessage"')
        cursor.execute('ALTER TABLE "chat_chatmessage_new" RENAME TO "chat_chatmessage"')

        cursor.execute('PRAGMA foreign_keys=ON')


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0006_room_membership'),
    ]

    operations = [
        migrations.RunPython(
            forwards_fix_chatmessage_user_fk,
            migrations.RunPython.noop,
        ),
    ]
