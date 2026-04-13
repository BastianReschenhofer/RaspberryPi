import os
from dotenv import load_dotenv
from flask import Flask, redirect, url_for, jsonify
from auth import auth_bp
from home import home_bp
from extensions import db, login_manager
from models import User

load_dotenv()

app = Flask(__name__)
app.config['ENV'] = 'development'
app.config['DEBUG'] = True

app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URI')

db.init_app(app)

login_manager.init_app(app)
login_manager.login_view = 'auth.login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(home_bp, url_prefix='/home')

@app.route('/')
def login():
    return redirect(url_for('auth.login'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()

        admin_user = os.getenv('ADMIN_USER')
        admin_pass = os.getenv('ADMIN_PASS')

        if not User.query.filter_by(username=admin_user).first():
                admin = User(username=admin_user)
                admin.set_password(admin_pass)
                db.session.add(admin)
                db.session.commit()
                print("Standard-Admin erstellt")
    app.run(port = 8080, debug = True)
