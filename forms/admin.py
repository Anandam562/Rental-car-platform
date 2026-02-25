# forms/admin.py
from flask_wtf import FlaskForm
from werkzeug.security import check_password_hash
from wtforms import StringField, PasswordField, SelectField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, Length

class AdminLoginForm(FlaskForm):
    """WTForm for admin login"""
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=80)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=3)])
    # Optional: Remember me checkbox
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Login as Admin')

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class AdminRegistrationForm(FlaskForm):
    """WTForm for admin registration (for super admins)"""
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=80)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=120)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=3)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired()])
    # Access level selection (only for super admins)
    access_level = SelectField('Access Level', choices=[
        ('support', 'Support'),
        ('finance', 'Finance'),
        ('content', 'Content Management'),
        ('super', 'Super Admin') # Exclude super admin from regular registration
    ], validators=[DataRequired()])
    is_active = BooleanField('Active', default=True)
    submit = SubmitField('Create Admin')
