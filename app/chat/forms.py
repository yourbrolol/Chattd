from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User

class UserForm(UserCreationForm):
    username = forms.CharField(required=True)
    class Meta:
        model = User
        fields = '__all__'
    