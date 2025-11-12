from flask import redirect, Blueprint, url_for, render_template, request

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        error = None
        
        username = request.form['nm']
        password = request.form['pw']
        
        if len(password) < 8:
            error = "Password needs at least 8 letters"
        
        elif len(username) < 3:
            error = "Username needs at least 3 letters"

        elif password[0] != password[0].upper():
            error = "First letter in password needs to be upper case!"

        if error:
            return render_template('login.html', error=error)
        else:
            return redirect(url_for('home.home'))
        
    else:
        return render_template('login.html')