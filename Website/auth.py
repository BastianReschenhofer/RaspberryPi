from flask import redirect, Blueprint, url_for, render_template, request

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        error = None

        username = 'admin'
        password = 'admin'

        try_username = request.form['nm']
        try_password = request.form['pw']


        
        if try_password != password or try_username != username:
            error = "Falsche Anmeldedaten"

        if error:
            return render_template('login.html', error=error)
        else:
            return redirect(url_for('home.home'))
        
    else:
        return render_template('login.html')