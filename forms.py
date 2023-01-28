from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, HiddenField
from wtforms.validators import DataRequired, URL
from flask_ckeditor import CKEditorField


class CreatePostForm(FlaskForm):
    title = StringField("Blog Post Title", validators=[DataRequired()])
    subtitle = StringField("Subtitle", validators=[DataRequired()])
    img_url = StringField("Blog Image URL", validators=[DataRequired(), URL()])
    body = CKEditorField("Blog Content", validators=[DataRequired()])
    csrf_token = HiddenField()
    submit = SubmitField("Submit Post")


class RegisterForm(FlaskForm):
    name = StringField("Your Name", validators=[DataRequired()])
    email = StringField("Your Email", validators=[DataRequired()])
    password = PasswordField("Your Password", validators=[DataRequired()])
    submit = SubmitField("Register")
    csrf_token = HiddenField()


class LoginForm(FlaskForm):
    email = StringField("Your Email", validators=[DataRequired()])
    password = PasswordField("Your Password", validators=[DataRequired()])
    submit = SubmitField("Login")
    csrf_token = HiddenField()


class CommentForm(FlaskForm):
    body = CKEditorField("Blog Content", validators=[DataRequired()])
    submit = SubmitField("Submit Comment")
    csrf_token = HiddenField()
