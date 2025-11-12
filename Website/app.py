from flask import Flask, redirect, url_for, jsonify
from auth import auth_bp
from home import home_bp
from extensions import db


app = Flask(__name__)
app.config['ENV'] = 'development'
app.config['DEBUG'] = True

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://user:1234@localhost/students_db'

db.init_app(app)


app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(home_bp, url_prefix='/home')

@app.route('/')
def login():
    return redirect(url_for('auth.login'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug = True)
