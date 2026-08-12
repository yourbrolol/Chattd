import logging

from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator

from .models import User, ChatRoom

logger = logging.getLogger(__name__)

class RegistrationForm(forms.Form):
    username = forms.CharField(
        max_length=20,
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'Username'}),
    )
    password = forms.CharField(
        required=True,
        widget=forms.PasswordInput(attrs={'placeholder': 'Password'}),
    )

    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).exists():
            raise ValidationError("This username is already taken.")
        return username

    def save(self):
        return User.objects.create_user(
            username=self.cleaned_data['username'],
            password=self.cleaned_data['password'],
        )

class LoginForm(forms.Form):
    username = forms.CharField(
        max_length=20,
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'Username'}),
    )
    password = forms.CharField(
        required=True,
        widget=forms.PasswordInput(attrs={'placeholder': 'Password'}),
    )

class RoomCreationForm(forms.Form):
    room_name = forms.CharField(
        max_length=20,
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'Username'}),
        validators=[
            RegexValidator(
                regex=r'^[a-zA-Z0-9._-]+$',
                message="Room name can only contain letters, numbers, hyphens, underscores, or periods.",
                code='invalid_room_name'
            )
        ]
    )
    room_type = forms.ChoiceField(
        choices=ChatRoom.RoomTypes.choices,
        initial=ChatRoom.RoomTypes.PUBLIC,
        widget=forms.Select(attrs={'class': 'form-control'})
    )