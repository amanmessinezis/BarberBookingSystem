import os
import pytest
from app import app, db, User, Barber, Customer, Barbershop, Service, Availability, Appointment
from werkzeug.security import generate_password_hash
from datetime import datetime, time


# Fixture to configure the test client and in-memory database
@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    client = app.test_client()

    with app.app_context():
        db.create_all()
        yield client
        db.drop_all()


# Fixture to set up initial database state with a barber, barbershop, service, availability, customer, and appointment
@pytest.fixture
def setup_database():
    with app.app_context():
        hashed_password = generate_password_hash("password", method='pbkdf2:sha256')
        barber = Barber(first_name="Barber", last_name="User", email="barber@example.com", password=hashed_password)
        db.session.add(barber)
        db.session.commit()

        barbershop = Barbershop(name="Test Barbershop", address="123 Barber St", phone_number="1234567890",
                                creator_id=barber.id)
        db.session.add(barbershop)
        db.session.commit()

        barber.shop_id = barbershop.shop_id
        db.session.commit()

        service = Service(barber_id=barber.id, name="Haircut", duration=30, price=25.0)
        db.session.add(service)
        db.session.commit()

        availability = Availability(barber_id=barber.id, date=datetime.today().date(), start_time=time(9, 0),
                                    end_time=time(17, 0))
        db.session.add(availability)
        db.session.commit()

        hashed_password = generate_password_hash("password", method='pbkdf2:sha256')
        customer = Customer(first_name="Customer", last_name="User", email="customer@example.com",
                            password=hashed_password)
        db.session.add(customer)
        db.session.commit()

        appointment = Appointment(
            barber_id=barber.id,
            customer_id=customer.id,
            service_id=service.id,
            customer_name=f"{customer.first_name} {customer.last_name}",
            date=datetime.today().date(),
            start_time=time(10, 0),
            end_time=time(10, 30)
        )
        db.session.add(appointment)
        db.session.commit()

        yield db


# Test case to update the time of an appointment
def test_update_appointment_time(client, setup_database):
    # Sign in as the customer
    client.post('/signin', data=dict(email="customer@example.com", password="password"), follow_redirects=True)

    # Verify the appointment in the customer home page
    response = client.get('/customer_home', follow_redirects=True)
    assert response.status_code == 200
    assert b"Your Appointments" in response.data
    assert b"Haircut" in response.data
    assert b"10:00" in response.data

    # Get the appointment id
    appointment = Appointment.query.first()

    # Update the time of the appointment
    response = client.post(f'/update_appointment/{appointment.id}', data=dict(start_time="11:00"),
                           follow_redirects=True)
    assert response.status_code == 200
    assert b"Appointment updated successfully" in response.data

    # Verify the updated appointment time in the customer home page
    response = client.get('/customer_home', follow_redirects=True)
    assert response.status_code == 200
    assert b"Your Appointments" in response.data
    assert b"Haircut" in response.data
    assert b"11:00" in response.data
