from flask import Blueprint, render_template, request, redirect, url_for
from flask_login import login_user, logout_user, current_user
from models import User

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['POST', 'GET'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home.home'))

    if request.method == 'POST':
        error = None
        
        try_username = request.form['nm']
        try_password = request.form['pw']

        user = User.query.filter_by(username=try_username).first()

        if user is None or not user.check_password(try_password):
            error = "Falsche Anmeldedaten"

        if error:
            return render_template('login.html', error=error)
        else:
            login_user(user)
            return redirect(url_for('home.home'))
        
    else:
        return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('auth.login'))