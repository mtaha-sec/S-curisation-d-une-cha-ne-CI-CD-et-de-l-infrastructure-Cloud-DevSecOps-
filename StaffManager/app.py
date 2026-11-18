import os
from pathlib import Path
from functools import wraps

from flask import Flask, render_template, redirect, url_for, flash, request, abort
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm, CSRFProtect
from wtforms import StringField, PasswordField, SelectField, SubmitField
from wtforms.validators import DataRequired, Length
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(40), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="employee")
    employee = db.relationship("Employee", backref="user", uselist=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Employee(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(60), nullable=False)
    last_name = db.Column(db.String(60), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    department = db.Column(db.String(80), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), unique=True)

class LoginForm(FlaskForm):
    username = StringField("Identifiant", validators=[DataRequired(), Length(max=40)])
    password = PasswordField("Mot de passe", validators=[DataRequired(), Length(max=128)])
    submit = SubmitField("Se connecter")

class EmployeeForm(FlaskForm):
    first_name = StringField("Prénom", validators=[DataRequired(), Length(max=60)])
    last_name = StringField("Nom", validators=[DataRequired(), Length(max=60)])
    email = StringField("Adresse e-mail", validators=[DataRequired(), Length(max=120)])
    department = StringField("Département", validators=[DataRequired(), Length(max=80)])
    submit = SubmitField("Enregistrer")

class UserForm(FlaskForm):
    username = StringField("Identifiant", validators=[DataRequired(), Length(min=3, max=40)])
    password = PasswordField("Mot de passe", validators=[DataRequired(), Length(min=12, max=128)])
    role = SelectField("Rôle", choices=[("admin", "Admin"), ("hr", "RH"), ("employee", "Employé")])
    submit = SubmitField("Créer le compte")

def create_app(test_config=None):
    app = Flask(__name__)
    app.config.update(
        SECRET_KEY=os.environ.get("SECRET_KEY"),
        SQLALCHEMY_DATABASE_URI=os.environ.get("DATABASE_URL", "sqlite:///staffmanager.db"),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=os.environ.get("COOKIE_SECURE", "false").lower() == "true",
        WTF_CSRF_TIME_LIMIT=3600,
    )
    if test_config:
        app.config.update(test_config)
    if not app.config.get("SECRET_KEY"):
        raise RuntimeError("SECRET_KEY doit être définie dans l'environnement.")

    db.init_app(app)
    csrf.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "login"
    login_manager.login_message = "Veuillez vous connecter pour accéder à cette page."
    login_manager.login_message_category = "warning"

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    def roles_required(*roles):
        def decorator(view):
            @wraps(view)
            @login_required
            def wrapped(*args, **kwargs):
                if current_user.role not in roles:
                    abort(403)
                return view(*args, **kwargs)
            return wrapped
        return decorator

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for("dashboard"))
        form = LoginForm()
        if form.validate_on_submit():
            user = User.query.filter_by(username=form.username.data.strip()).first()
            if user and user.check_password(form.password.data):
                login_user(user)
                next_url = request.args.get("next", "")
                # Only allow local relative redirects to prevent open redirects.
                if next_url.startswith("/") and not next_url.startswith("//"):
                    return redirect(next_url)
                return redirect(url_for("dashboard"))
            flash("Identifiant ou mot de passe incorrect.", "danger")
        return render_template("login.html", form=form)

    @app.post("/logout")
    @login_required
    def logout():
        logout_user()
        flash("Vous êtes déconnecté.", "success")
        return redirect(url_for("login"))

    @app.get("/")
    @login_required
    def dashboard():
        total = Employee.query.count() if current_user.role in ("admin", "hr") else 0
        return render_template("dashboard.html", total=total)

    @app.route("/employees", methods=["GET", "POST"])
    @roles_required("admin", "hr")
    def employees():
        form = EmployeeForm()
        if form.validate_on_submit():
            email = form.email.data.strip().lower()
            if Employee.query.filter_by(email=email).first():
                flash("Cette adresse e-mail existe déjà.", "danger")
            else:
                employee = Employee(
                    first_name=form.first_name.data.strip(),
                    last_name=form.last_name.data.strip(),
                    email=email,
                    department=form.department.data.strip(),
                )
                db.session.add(employee)
                db.session.commit()
                flash("Employé ajouté.", "success")
                return redirect(url_for("employees"))
        records = Employee.query.order_by(Employee.last_name.asc()).all()
        return render_template("employees.html", form=form, employees=records)

    @app.route("/users/new", methods=["GET", "POST"])
    @roles_required("admin")
    def create_user():
        form = UserForm()
        if form.validate_on_submit():
            username = form.username.data.strip()
            if User.query.filter_by(username=username).first():
                flash("Cet identifiant existe déjà.", "danger")
            else:
                user = User(username=username, role=form.role.data)
                user.set_password(form.password.data)
                db.session.add(user)
                db.session.commit()
                flash("Compte créé. Associez ensuite le compte à un employé depuis l'administration.", "success")
                return redirect(url_for("dashboard"))
        return render_template("user_new.html", form=form)

    @app.get("/my-profile")
    @login_required
    def my_profile():
        return render_template("profile.html", employee=current_user.employee)

    @app.errorhandler(403)
    def forbidden(_error):
        return render_template("error.html", code=403, message="Vous n'avez pas les droits nécessaires."), 403

    @app.errorhandler(404)
    def not_found(_error):
        return render_template("error.html", code=404, message="Cette page n'existe pas."), 404

    with app.app_context():
        db.create_all()
        # Bootstrap the first admin only when credentials are explicitly supplied.
        admin_username = os.environ.get("ADMIN_USERNAME")
        admin_password = os.environ.get("ADMIN_PASSWORD")
        if admin_username and admin_password and not User.query.filter_by(role="admin").first():
            if len(admin_password) < 12:
                raise RuntimeError("ADMIN_PASSWORD doit contenir au moins 12 caractères.")
            admin = User(username=admin_username, role="admin")
            admin.set_password(admin_password)
            db.session.add(admin)
            db.session.commit()

    return app

app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
