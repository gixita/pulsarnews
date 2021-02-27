from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField, BooleanField, IntegerField
from wtforms.validators import (
    ValidationError,
    DataRequired,
    Email,
    Length,
    URL,
    Optional,
)
from app.models import User

class EditUserForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    about_me = TextAreaField("About me", validators=[Length(min=0, max=140)])
    email = StringField("Email", validators=[DataRequired(), Email()])
    company_id = IntegerField("Company ID", validators=[DataRequired()])
    verified = BooleanField(label="Is verified")
    admin = BooleanField(label="Is admin")
    banned = BooleanField(label="Is banned")
    
    submit = SubmitField("Submit")

    def __init__(self, original_username,  *args, **kwargs):
        super(EditUserForm, self).__init__(*args, **kwargs)
        self.original_username = original_username

class EditCompanyForm(FlaskForm):
    name = StringField("Company name", validators=[DataRequired()])
    banned = BooleanField(label="Is banned")
    premium = BooleanField(label="Is premium")
    subdomain = StringField("Subdomain")
    type_of_auth = StringField("Type of authentication")
    tenant = StringField("Tenant")
    client_id = StringField("Client ID")
    client_secret = StringField("Client secret")
    resource = StringField("Resource")
    callback_path = StringField("Callback path")
    authority = StringField("Authority")
    redirect_path = StringField("Redirect path")
    endpoint = StringField("Endpoint")
    scope = StringField("Scope")
    submit = SubmitField("Save")

    def __init__(self, original_username,  *args, **kwargs):
        super(EditCompanyForm, self).__init__(*args, **kwargs)
        self.original_username = original_username

class AddCompanyForm(FlaskForm):
    name = StringField("Company name", validators=[DataRequired()])
    submit = SubmitField("Save")

    def __init__(self,  *args, **kwargs):
        super(AddCompanyForm, self).__init__(*args, **kwargs)

class EditDomainForm(FlaskForm):
    name = StringField("Domain name", validators=[DataRequired()])
    company_id = IntegerField("Company ID", validators=[DataRequired()])
    fully_managed_domain = BooleanField(label="Is a fully managed domain")
    submit = SubmitField("Save")

    def __init__(self, original_username,  *args, **kwargs):
        super(EditDomainForm, self).__init__(*args, **kwargs)
        self.original_username = original_username

class EditPostForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired()])
    url = StringField("URL", validators=[DataRequired()])
    url_base = StringField("URL base - via", validators=[DataRequired()])
    text = TextAreaField("Text", validators=[Length(min=0, max=1000)])
    user_id = IntegerField("User ID", validators=[DataRequired()])
    deleted = BooleanField(label="Is deleted")
    company_id = IntegerField("Company ID", validators=[DataRequired()])
    submit = SubmitField("Save")

    def __init__(self, original_username,  *args, **kwargs):
        super(EditPostForm, self).__init__(*args, **kwargs)
        self.original_username = original_username
