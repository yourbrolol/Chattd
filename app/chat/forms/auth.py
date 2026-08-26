from wtforms import Form, StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length, Email, EqualTo
from app.core.settings import settings

class RegistrationForm(Form):
    username = StringField(
        "Username",
        validators=[DataRequired(), Length(min=settings.USERNAME_MIN_LENGTH, max=settings.USERNAME_MAX_LENGTH)]
    )

    password = PasswordField(
        "Password",
        validators=[DataRequired(), Length(min=settings.PASSWORD_MIN_LENGTH, max=settings.PASSWORD_MAX_LENGTH)]
    )

class LoginForm(Form):
    username = StringField(
        "Username",
        validators=[DataRequired(), Length(min=settings.USERNAME_MIN_LENGTH, max=settings.USERNAME_MAX_LENGTH)]
    )

    password = PasswordField(
        "Password",
        validators=[DataRequired(), Length(min=settings.PASSWORD_MIN_LENGTH, max=settings.PASSWORD_MAX_LENGTH)]
    )