import pytest
from app import app, db
from app import User, Barber, Service, Availability
from datetime import datetime, date
from werkzeug.security import generate_password_hash


@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    client = app.test_client()

    with app.app_context():
        db.create_all()
        yield client
        db.drop_all()


def test_book_appointment(client):
    hashed_password = generate_password_hash("testpassword", method='pbkdf2:sha256')
    barber = Barber(first_name="Barber", last_name="Test", email="barber@test.com", password=hashed_password)
    customer = User(first_name="Customer", last_name="Test", email="customer@test.com", password=hashed_password,
                    type="customer")
    db.session.add(barber)
    db.session.add(customer)
    db.session.commit()

    service = Service(barber_id=barber.id, name="Haircut", duration=30, price=20.0)
    db.session.add(service)
    db.session.commit()

    availability = Availability(barber_id=barber.id, date=date(2024, 7, 1),
                                start_time=datetime.strptime("09:00", "%H:%M").time(),
                                end_time=datetime.strptime("17:00", "%H:%M").time())
    db.session.add(availability)
    db.session.commit()

    # Log in as the customer
    client.post('/signin', data=dict(email="customer@test.com", password="testpassword"), follow_redirects=True)

    response = client.get(f'/book_appointment/{service.id}')
    assert response.status_code == 200
    assert b"Book Appointment for Haircut" in response.data
