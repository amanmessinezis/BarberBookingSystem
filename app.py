import os
from datetime import datetime, timedelta

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

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


class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    service_id = db.Column(db.Integer, db.ForeignKey('service.id', ondelete='CASCADE'), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id', ondelete='CASCADE'), nullable=False)
    barber_id = db.Column(db.Integer, db.ForeignKey('barber.id', ondelete='CASCADE'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)


class Availability(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    barber_id = db.Column(db.Integer, db.ForeignKey('barber.id', ondelete='CASCADE'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)

    def __init__(self, barber_id, date, start_time, end_time):
        self.barber_id = barber_id
        self.date = date
        self.start_time = start_time
        self.end_time = end_time


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


class Service(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    barber_id = db.Column(db.Integer, db.ForeignKey('barber.id', ondelete='CASCADE'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    duration = db.Column(db.Integer, nullable=False)  # Duration in minutes
    price = db.Column(db.Float, nullable=False)

    def __init__(self, barber_id, name, duration, price):
        self.barber_id = barber_id
        self.name = name
        self.duration = duration
        self.price = price


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


@app.route('/customer_search_barbershop', methods=['GET'])
@login_required
def customer_search_barbershop():
    search_query = request.args.get('search')
    barbershops = Barbershop.query.filter(Barbershop.name.contains(search_query)).all()
    return render_template('customer_home.html', barbershops=barbershops)


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

    services = Service.query.filter_by(barber_id=current_user.id).all()
    availabilities = Availability.query.filter_by(barber_id=current_user.id).all()

    return render_template('barber_home.html', barbershops=barbershops, barbershop=barbershop,
                           services=services, availabilities=availabilities)


@app.route('/book_appointment/<int:service_id>', methods=['GET'])
@login_required
def book_appointment(service_id):
    service = Service.query.get_or_404(service_id)
    barber = Barber.query.get(service.barber_id)
    availabilities = Availability.query.filter_by(barber_id=barber.id).all()
    available_days = []

    for availability in availabilities:
        availability_duration = (datetime.combine(datetime.min, availability.end_time) -
                                 datetime.combine(datetime.min, availability.start_time)).seconds // 60
        if availability_duration >= service.duration:
            available_days.append(availability.date)

    return render_template('book_appointment.html', service=service, barber=barber, available_days=available_days)


@app.route('/choose_time/<int:service_id>/<date>', methods=['GET', 'POST'])
@login_required
def choose_time(service_id, date):
    service = Service.query.get_or_404(service_id)
    barber = Barber.query.get(service.barber_id)
    availabilities = Availability.query.filter_by(barber_id=barber.id, date=date).all()
    existing_appointments = Appointment.query.filter_by(barber_id=barber.id, date=date).all()

    if request.method == 'POST':
        start_time_str = request.form['start_time']
        start_time = datetime.strptime(start_time_str, '%H:%M').time()
        end_time = (datetime.combine(datetime.min, start_time) + timedelta(minutes=service.duration)).time()

        # Check if the selected time is within the barber's availability and not overlapping with existing appointments
        for availability in availabilities:
            if start_time >= availability.start_time and end_time <= availability.end_time:
                overlap = False
                for appointment in existing_appointments:
                    if (start_time < appointment.end_time and end_time > appointment.start_time):
                        overlap = True
                        break

                if not overlap:
                    new_appointment = Appointment(
                        service_id=service.id,
                        customer_id=current_user.id,
                        barber_id=barber.id,
                        date=datetime.strptime(date, '%Y-%m-%d').date(),
                        start_time=start_time,
                        end_time=end_time
                    )
                    db.session.add(new_appointment)
                    db.session.commit()
                    flash('Appointment confirmed.', 'success')
                    return redirect(url_for('customer_home'))

        flash('Selected time is not available. Please choose another time.', 'error')

    return render_template('choose_time.html', service=service, barber=barber, date=date)


@app.route('/api/availability/<int:barber_id>/<date>')
@login_required
def api_availability(barber_id, date):
    availabilities = Availability.query.filter_by(barber_id=barber_id, date=date).all()
    appointments = Appointment.query.filter_by(barber_id=barber_id, date=date).all()
    events = []

    for availability in availabilities:
        events.append({
            'title': 'Available',
            'start': f"{availability.date}T{availability.start_time}",
            'end': f"{availability.date}T{availability.end_time}"
        })

    for appointment in appointments:
        events.append({
            'title': 'Booked',
            'start': f"{appointment.date}T{appointment.start_time}",
            'end': f"{appointment.date}T{appointment.end_time}",
            'color': 'red'  # Optional: to distinguish booked slots
        })

    return jsonify(events)


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


@app.route('/barber_calendar')
@login_required
def barber_calendar():
    if current_user.type != 'barber':
        flash('You do not have access to this page.', 'error')
        return redirect(url_for('customer_home'))

    return render_template('barber_calendar.html', barber_id=current_user.id)


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
    if current_user.shop_id:
        flash('You are already associated with a barbershop.', 'error')
        return redirect(url_for('barber_home'))

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
        flash('You cannot search for a barbershop because you are already associated with one.'
              , 'error')
        return redirect(url_for('barber_home'))

    search_query = request.args.get('search')
    barbershops = Barbershop.query.filter(Barbershop.name.contains(search_query)).all()
    return render_template('barber_home.html', barbershops=barbershops)


@app.route('/view_barbers/<int:shop_id>', methods=['GET'])
@login_required
def view_barbers(shop_id):
    barbershop = Barbershop.query.get_or_404(shop_id)
    barbers = Barber.query.filter_by(shop_id=shop_id).all()
    barber_services = {}

    for barber in barbers:
        services = Service.query.filter_by(barber_id=barber.id).all()
        barber_services[barber.id] = services

    return render_template('view_barbers.html', barbershop=barbershop, barbers=barbers,
                           barber_services=barber_services)


@app.route('/leave_barbershop/<int:shop_id>', methods=['POST'])
@login_required
def leave_barbershop(shop_id):
    if current_user.shop_id != shop_id:
        flash('You cannot leave a barbershop you are not associated with.', 'error')
        return redirect(url_for('barber_home'))

    barbershop = Barbershop.query.get_or_404(shop_id)
    if barbershop.creator_id == current_user.id:
        flash('You cannot leave a barbershop you created. Delete the barbershop instead.', 'error')
        return redirect(url_for('barber_home'))

    current_user.shop_id = None

    try:
        db.session.commit()
        flash('You have left the barbershop.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'There was an issue leaving the barbershop: {e}', 'error')

    return redirect(url_for('barber_home'))


@app.route('/update_service/<int:service_id>', methods=['GET', 'POST'])
@login_required
def update_service(service_id):
    service = Service.query.get_or_404(service_id)
    if service.barber_id != current_user.id:
        flash('You do not have permission to update this service.', 'error')
        return redirect(url_for('barber_home'))

    if request.method == 'POST':
        service.name = request.form['name']
        service.duration = request.form['duration']
        service.price = request.form['price']

        try:
            db.session.commit()
            flash('Service updated successfully.', 'success')
            return redirect(url_for('barber_home'))
        except Exception as e:
            db.session.rollback()
            flash(f'There was an issue updating the service: {e}', 'error')
            return redirect(url_for('update_service', service_id=service_id))

    return render_template('update_service.html', service=service)


@app.route('/delete_service/<int:service_id>', methods=['POST'])
@login_required
def delete_service(service_id):
    service = Service.query.get_or_404(service_id)
    if service.barber_id != current_user.id:
        flash('You do not have permission to delete this service.', 'error')
        return redirect(url_for('barber_home'))

    try:
        db.session.delete(service)
        db.session.commit()
        flash('Service deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'There was an issue deleting the service: {e}', 'error')

    return redirect(url_for('barber_home'))


@app.route('/update_availability/<int:availability_id>', methods=['GET', 'POST'])
@login_required
def update_availability(availability_id):
    availability = Availability.query.get_or_404(availability_id)
    if availability.barber_id != current_user.id:
        flash('You do not have permission to update this availability.', 'error')
        return redirect(url_for('barber_home'))

    if request.method == 'POST':
        availability.date = datetime.strptime(request.form['date'], '%Y-%m-%d').date()
        # Ensure seconds are stripped from the time string before parsing
        start_time_str = request.form['start_time']
        end_time_str = request.form['end_time']
        availability.start_time = datetime.strptime(start_time_str,
                                                    '%H:%M:%S' if ':' in start_time_str else '%H:%M').time()
        availability.end_time = datetime.strptime(end_time_str, '%H:%M:%S' if ':' in end_time_str else '%H:%M').time()

        try:
            db.session.commit()
            flash('Availability updated successfully.', 'success')
            return redirect(url_for('barber_home'))
        except Exception as e:
            db.session.rollback()
            flash(f'There was an issue updating the availability: {e}', 'error')
            return redirect(url_for('update_availability', availability_id=availability_id))

    return render_template('update_availability.html', availability=availability)


@app.route('/delete_availability/<int:availability_id>', methods=['POST'])
@login_required
def delete_availability(availability_id):
    availability = Availability.query.get_or_404(availability_id)
    if availability.barber_id != current_user.id:
        flash('You do not have permission to delete this availability.', 'error')
        return redirect(url_for('barber_home'))

    try:
        db.session.delete(availability)
        db.session.commit()
        flash('Availability deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'There was an issue deleting the availability: {e}', 'error')

    return redirect(url_for('barber_home'))


@app.route('/api/events')
@login_required
def get_events():
    availabilities = Availability.query.filter_by(barber_id=current_user.id).all()
    events = []

    for availability in availabilities:
        events.append({
            'title': 'Available',
            'start': f"{availability.date}T{availability.start_time}",
            'end': f"{availability.date}T{availability.end_time}"
        })

    return jsonify(events)


@app.route('/calendar')
@login_required
def calendar():
    return render_template('calendar.html')


@app.route('/add_availability')
@login_required
def add_availability():
    return render_template('add_availability.html')


@app.route('/save_availability', methods=['POST'])
@login_required
def save_availability():
    date_str = request.form['date']
    start_time_str = request.form['start_time']
    end_time_str = request.form['end_time']

    try:
        date = datetime.strptime(date_str, '%Y-%m-%d').date()
        start_time = datetime.strptime(start_time_str, '%H:%M').time()
        end_time = datetime.strptime(end_time_str, '%H:%M').time()

        new_availability = Availability(
            barber_id=current_user.id,
            date=date,
            start_time=start_time,
            end_time=end_time
        )

        db.session.add(new_availability)
        db.session.commit()
        flash('Availability added successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'There was an issue adding your availability: {e}', 'error')

    return redirect(url_for('barber_home'))


@app.route('/add_service')
@login_required
def add_service():
    return render_template('add_service.html')


@app.route('/save_service', methods=['POST'])
@login_required
def save_service():
    name = request.form['name']
    duration = request.form['duration']
    price = request.form['price']

    try:
        new_service = Service(
            barber_id=current_user.id,
            name=name,
            duration=int(duration),
            price=float(price)
        )

        db.session.add(new_service)
        db.session.commit()
        flash('Service added successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'There was an issue adding your service: {e}', 'error')

    return redirect(url_for('barber_home'))


@app.route('/services')
@login_required
def services():
    services = Service.query.filter_by(barber_id=current_user.id).all()
    return render_template('services.html', services=services)


@app.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    flash('You have been logged out successfully.', 'success')
    return redirect(url_for('signin'))


if __name__ == '__main__':
    app.run(debug=True)
