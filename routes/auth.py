from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required
# routes/auth.py (Relevant part - register function)
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.fields.simple import BooleanField
from wtforms.validators import DataRequired, Email, Length
from models.user import User, db

auth_bp = Blueprint('auth', __name__)


class RegistrationForm(FlaskForm):
    """WTForm for user registration"""
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=80)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=120)])
    phone = StringField('Phone', validators=[DataRequired(), Length(min=10, max=20)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    submit = SubmitField('Register')


# --- CRITICAL FIX 2: Define LoginForm using WTForms ---
class LoginForm(FlaskForm):
    """WTForm for user login"""
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')
# --- END CRITICAL FIX 2 ---

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    User login page.
    This is the 'auth.login' endpoint.
    """
    # --- CRITICAL FIX 3: Instantiate the LoginForm ---
    form = LoginForm()  # Create an instance of the form
    # --- END CRITICAL FIX 3 ---

    if request.method == 'POST':
        # --- CRITICAL FIX 4: Use form validation ---
        # BEFORE (Manual validation)
        # email = request.form['email']
        # password = request.form['password']
        # remember = bool(request.form.get('remember_me'))
        # user = User.query.filter_by(email=email).first()
        # if user and user.check_password(password):
        #     login_user(user, remember=remember)
        #     return redirect(url_for('car.home'))
        # else:
        #     flash('Invalid email or password')

        # AFTER (WTForms validation)
        if form.validate_on_submit():  # This checks CSRF token and other validations
            email = form.email.data.strip().lower()
            password = form.password.data
            remember = form.remember_me.data

            user = User.query.filter_by(email=email).first()

            if user and user.check_password(password):
                login_user(user, remember=remember)
                flash('Login successful!', 'success')
                # Redirect to next page or car home
                next_page = request.args.get('next')
                return redirect(next_page) if next_page else redirect(url_for('car.home'))
            else:
                flash('Invalid email or password.', 'danger')
        else:
            # Form validation failed (CSRF, missing fields, etc.)
            flash('Please check your input and try again.', 'danger')
        # --- END CRITICAL FIX 4 ---

    # For GET request or failed validation, render the form
    # Pass the form instance to the template
    return render_template('login.html', form=form)  # <-- Pass the form instance





@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """User registration page"""
    form = RegistrationForm()  # Instantiate the form

    if form.validate_on_submit():  # This checks CSRF token and other validations
        username = form.username.data.strip()
        email = form.email.data.strip().lower()
        phone = form.phone.data.strip()
        password = form.password.data

        # Check if user exists
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'danger')
            return render_template('register.html', form=form)  # Pass form back

        # Create new user
        user = User(username=username, email=email, phone=phone)
        user.set_password(password)
        db.session.add(user)

        try:
            db.session.commit()
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error during registration: {str(e)}', 'danger')
            return render_template('register.html', form=form)  # Pass form back

    # For GET request or failed validation, render the form
    # Pre-populate form with request data if available (for errors)
    return render_template('register.html', form=form)  # Pass the form instance


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('car.home'))