from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///BBS.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your_secret_key'
db = SQLAlchemy(app)


class User(db.Model):
    uid = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)


with app.app_context():
    db.create_all()


@app.route('/', methods=['POST', 'GET'])
def index():
    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password != confirm_password:
            return 'Passwords do not match'

        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        new_user = User(first_name=first_name, last_name=last_name, email=email, password=hashed_password)

        try:
            db.session.add(new_user)
            db.session.commit()
            return redirect(url_for('signin'))
        except Exception as e:
            db.session.rollback()
            return f'There was an issue adding your account: {e}'
    else:
        return render_template('index.html')


@app.route('/signin', methods=['POST', 'GET'])
def signin():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            return 'Signed in successfully!'
        else:
            flash('Invalid email or password')
            return redirect(url_for('signin'))
    else:
        return render_template('signin.html')


if __name__ == '__main__':
    app.run(debug=True)
