from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField, BooleanField
from wtforms.validators import (
    ValidationError,
    DataRequired,
    Email,
    Length,
    URL,
    Optional,
)
from app.models import User


class EditProfileForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    about_me = TextAreaField("About me", validators=[Length(min=0, max=140)])
    # email = StringField("Email", validators=[DataRequired(), Email()])
    submit = SubmitField("Submit")

    def __init__(self, original_username,  *args, **kwargs):
        super(EditProfileForm, self).__init__(*args, **kwargs)
        self.original_username = original_username
        # self.original_email = original_email

    # def validate_username(self, username):
    #     if username.data != self.original_username:
    #         user = User.query.filter_by(username=self.username.data).first()
    #         if user is not None:
    #             raise ValidationError("Please use a different username.")

    # def validate_email(self, email):
    #     if email.data != self.original_email:
    #         user = User.query.filter_by(email=self.email.data).first()
    #         if user is not None:
    #             raise ValidationError("Please use a different email.")


class PostForm(FlaskForm):
    title = StringField(
        "Title", validators=[DataRequired(), Length(min=1, max=240)]
    )
    text = TextAreaField(
        "Description and what's the impact for your company (optional)", validators=[Optional(), Length(min=1, max=1000)]
    )
    url = StringField("URL", validators=[DataRequired(), URL()])
    submit = SubmitField("Submit")

    def validate_text(self, text):
        if len(self.url.data) < 0:
            raise ValidationError("Please choose text or link post.")

    def validate_url(self, url):
        if len(self.text.data) < 0:
            raise ValidationError("Please choose text or link post.")


class CommentForm(FlaskForm):
    text = TextAreaField(
        "Comment post", validators=[DataRequired(), Length(min=1, max=1000)]
    )
    submit = SubmitField("Add Comment")


class AddDomainForm(FlaskForm):
    name = StringField("Mail domain", validators=[DataRequired()])
    fully_managed_domain = BooleanField("This domain is used <b>only</b> by my company")
    submit = SubmitField("Add email domain")
