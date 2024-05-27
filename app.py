import os
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_migrate import Migrate

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///BBS.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'default_secret_key')  # Fallback to default if not set

db = SQLAlchemy(app)
migrate = Migrate(app, db)

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
    id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), primary_key=True)

    __mapper_args__ = {
        'polymorphic_identity': 'customer',
    }

    def __init__(self, first_name, last_name, email, password):
        super().__init__(first_name, last_name, email, password, type='customer')


class Barber(User):
    __tablename__ = 'barber'
    id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), primary_key=True)
    shop_id = db.Column(db.Integer, db.ForeignKey('barbershop.shop_id', ondelete='SET NULL'), nullable=True)

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
    creator_id = db.Column(db.Integer, db.ForeignKey('barber.id', ondelete='SET NULL'), unique=True)

    def __init__(self, name, address, phone_number, creator_id):
        self.name = name
        self.address = address
        self.phone_number = phone_number
        self.creator_id = creator_id


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
    if current_user.is_authenticated:
        if current_user.type == 'customer':
            return redirect(url_for('customer_home'))
        elif current_user.type == 'barber':
            return redirect(url_for('barber_home'))
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
    barbershops = []
    search_query = request.args.get('search')
    if search_query and not current_user.shop_id:
        barbershops = Barbershop.query.filter(Barbershop.name.contains(search_query)).all()

    barbershop = None
    if current_user.shop_id:
        barbershop = Barbershop.query.get(current_user.shop_id)

    return render_template('barber_home.html', barbershops=barbershops, barbershop=barbershop)


@app.route('/new_barbershop', methods=['POST'])
@login_required
def new_barbershop():
    if current_user.shop_id:
        flash('You cannot create a new barbershop because you are already associated with one.', 'error')
        return redirect(url_for('barber_home'))

    name = request.form['name']
    address = request.form['address']
    phone_number = request.form['phone_number']
    new_shop = Barbershop(name=name, address=address, phone_number=phone_number, creator_id=current_user.id)

    try:
        db.session.add(new_shop)
        db.session.commit()
        current_user.shop_id = new_shop.shop_id
        db.session.commit()
        flash('Barbershop created successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'There was an issue creating the barbershop: {e}', 'error')

    return redirect(url_for('barber_home'))


@app.route('/update_barbershop/<int:shop_id>', methods=['GET', 'POST'])
@login_required
def update_barbershop(shop_id):
    shop = Barbershop.query.get_or_404(shop_id)
    if shop.creator_id != current_user.id:
        flash('You do not have permission to update this barbershop.', 'error')
        return redirect(url_for('barber_home'))

    if request.method == 'POST':
        shop.name = request.form['name']
        shop.address = request.form['address']
        shop.phone_number = request.form['phone_number']

        try:
            db.session.commit()
            flash('Barbershop updated successfully.', 'success')
            return redirect(url_for('barber_home'))
        except Exception as e:
            db.session.rollback()
            flash(f'There was an issue updating the barbershop: {e}', 'error')
            return redirect(url_for('update_barbershop', shop_id=shop_id))

    return render_template('update_barbershop.html', shop=shop)


@app.route('/delete_barbershop/<int:shop_id>', methods=['POST'])
@login_required
def delete_barbershop(shop_id):
    shop = Barbershop.query.get_or_404(shop_id)
    if shop.creator_id != current_user.id:
        flash('You do not have permission to delete this barbershop.', 'error')
        return redirect(url_for('barber_home'))

    try:
        db.session.delete(shop)
        db.session.commit()
        if current_user.shop_id == shop_id:
            current_user.shop_id = None
            db.session.commit()
        flash('Barbershop deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'There was an issue deleting the barbershop: {e}', 'error')

    return redirect(url_for('barber_home'))


@app.route('/join_barbershop/<int:shop_id>', methods=['POST'])
@login_required
def join_barbershop(shop_id):
    barbershop = Barbershop.query.get_or_404(shop_id)
    current_user.shop_id = barbershop.shop_id

    try:
        db.session.commit()
        flash('Joined barbershop successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'There was an issue joining the barbershop: {e}', 'error')

    return redirect(url_for('barber_home'))


@app.route('/search_barbershop', methods=['GET'])
@login_required
def search_barbershop():
    if current_user.shop_id:
        flash('You cannot search for a barbershop because you are already associated with one.', 'error')
        return redirect(url_for('barber_home'))

    search_query = request.args.get('search')
    barbershops = Barbershop.query.filter(Barbershop.name.contains(search_query)).all()
    return render_template('barber_home.html', barbershops=barbershops)


@app.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('signin'))


if __name__ == '__main__':
    app.run(debug=True)
