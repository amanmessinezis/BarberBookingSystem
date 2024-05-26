import os
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///BBS.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'default_secret_key')  # Fallback to default if not set

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'signin'


class User(db.Model, UserMixin):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(50))

    __mapper_args__ = {
        'polymorphic_identity': 'user',
        'polymorphic_on': type
    }

    def __init__(self, first_name, last_name, email, password, type):
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.password = password
        self.type = type


class Customer(User):
    __tablename__ = 'customer'
    id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)

    __mapper_args__ = {
        'polymorphic_identity': 'customer',
    }

    def __init__(self, first_name, last_name, email, password):
        super().__init__(first_name, last_name, email, password, type='customer')


class Barber(User):
    __tablename__ = 'barber'
    id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    shop_id = db.Column(db.Integer, db.ForeignKey('barbershop.shop_id'), nullable=True)

    __mapper_args__ = {
        'polymorphic_identity': 'barber',
    }

    def __init__(self, first_name, last_name, email, password, shopid=None):
        super().__init__(first_name, last_name, email, password, type='barber')
        self.shop_id = shopid


class Barbershop(db.Model):
    __tablename__ = 'barbershop'
    shop_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(200), nullable=False)
    phone_number = db.Column(db.String(15), nullable=False)

    def __init__(self, name, address, phone_number):
        self.name = name
        self.address = address
        self.phone_number = phone_number


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


with app.app_context():
    db.create_all()


@app.route('/', methods=['POST', 'GET'])
def index():
    if current_user.is_authenticated:
        if current_user.type == 'customer':
            return redirect(url_for('customer_home'))
        elif current_user.type == 'barber':
            return redirect(url_for('barber_home'))
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
            flash('Account created successfully. Please sign in.', 'success')
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
            login_user(user)
            if user.type == 'customer':
                return redirect(url_for('customer_home'))
            elif user.type == 'barber':
                return redirect(url_for('barber_home'))
            else:
                flash('Invalid user type.', 'error')
                return redirect(url_for('signin'))
        else:
            flash('Invalid email or password', 'error')
            return redirect(url_for('signin'))
    else:
        return render_template('signin.html')


@app.route('/customer_home')
@login_required
def customer_home():
    return render_template('customer_home.html')


@app.route('/barber_home')
@login_required
def barber_home():
    return render_template('barber_home.html')


@app.route('/new_barbershop', methods=['GET', 'POST'])
@login_required
def new_barbershop():
    if request.method == 'POST':
        name = request.form['name']
        address = request.form['address']
        phone_number = request.form['phone_number']
        default_barber = 'default_barber' in request.form

        new_shop = Barbershop(name=name, address=address, phone_number=phone_number)

        try:
            db.session.add(new_shop)
            db.session.commit()
            if default_barber and current_user.type == 'barber':
                current_user.shop_id = new_shop.shop_id
                db.session.commit()
            flash('Barbershop added successfully.', 'success')
            return redirect(url_for('barber_home'))
        except Exception as e:
            db.session.rollback()
            flash(f'There was an issue adding the barbershop: {e}', 'error')
            return redirect(url_for('new_barbershop'))
    else:
        return render_template('new_barbershop.html')


@app.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('signin'))


if __name__ == '__main__':
    app.run(debug=True)
