from django.db import models

class ChatMessage(models.Model):
    room = models.CharField()
    content = models.TextField()
    timestamp = models.TimeField(auto_now_add=True)

    def __str__(self):
        return f"[{self.room}] {self.content[:30]}"