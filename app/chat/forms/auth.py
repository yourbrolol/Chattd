from wtforms import Form, StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length, Email, EqualTo

class RegistrationForm(Form):
    username = StringField(
        "Username",
        validators=[DataRequired(), Length(min=3, max=32)]
    )

    password = PasswordField(
        "Password",
        validators=[DataRequired(), Length(min=8, max=72)]
    )

class LoginForm(Form):
    username = StringField(
        "Username",
        validators=[DataRequired(), Length(min=1, max=20)]
    )

    password = PasswordField(
        "Password",
        validators=[DataRequired(), Length(min=8, max=72)]
    )