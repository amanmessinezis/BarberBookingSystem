import os
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///BBS.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'default_secret_key')  # Fallback to default if not set

db = SQLAlchemy(app)


class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(50))

    __mapper_args__ = {
        'polymorphic_identity': 'user',  # Base type
        'polymorphic_on': type  # Column used to distinguish between types
    }


class Customer(User):
    __tablename__ = 'customer'
    id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)

    __mapper_args__ = {
        'polymorphic_identity': 'customer',  # Identity for Customer
    }


class Barber(User):
    __tablename__ = 'barber'
    id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    shop_id = db.Column(db.Integer, nullable=True)

    __mapper_args__ = {
        'polymorphic_identity': 'barber',  # Identity for Barber
    }


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
        user_type = request.form['user_type']

        # Check if the email already exists
        existing_user = User.query.filter_by(email=email).first()

        if existing_user:
            flash('An account with this email already exists.', 'error')
            return redirect(url_for('index'))

        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return redirect(url_for('index'))

        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

        if user_type == 'customer':
            new_user = Customer(first_name=first_name, last_name=last_name, email=email, password=hashed_password)
        elif user_type == 'barber':
            new_user = Barber(first_name=first_name, last_name=last_name, email=email, password=hashed_password)
        else:
            flash('Invalid user type selected.', 'error')
            return redirect(url_for('index'))

        try:
            db.session.add(new_user)
            db.session.commit()
            flash('Account created successfully! Please sign in.', 'success')
            return redirect(url_for('signin'))
        except Exception as e:
            db.session.rollback()
            flash(f'There was an issue adding your account: {e}', 'error')
            return redirect(url_for('index'))
    else:
        return render_template('index.html')


@app.route('/signin', methods=['POST', 'GET'])
def signin():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            return 'Signed in successfully!'  # Add dashboard redirection or logic here
        else:
            flash('Invalid email or password', 'error')
            return redirect(url_for('signin'))
    else:
        return render_template('signin.html')


if __name__ == '__main__':
    app.run(debug=True)
