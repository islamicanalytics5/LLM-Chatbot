from django.db import models
from accounts.models import CustomUser  # Importing your CustomUser model

class ChatHistory(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)  # Linking to your custom user model
    prompt = models.TextField(null=True, blank=True)       
    response = models.TextField(null=True, blank=True)     
    model_name = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        prompt_preview = (self.prompt[:50] + '...') if len(self.prompt) > 50 else self.prompt
        return f"Chat {self.id} by {self.user.username}: {prompt_preview}"
