import os
import pytest
from app import app, db
from app import User, Barber


@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    client = app.test_client()

    with app.app_context():
        db.create_all()
        yield client
        db.drop_all()


def test_create_barber_account(client):
    response = client.post('/', data=dict(
        first_name="Barber",
        last_name="User",
        email="barber@example.com",
        password="password",
        confirm_password="password",
        user_type="barber"
    ), follow_redirects=True)
    assert response.status_code == 200
    assert b"Account created successfully" in response.data

    barber = Barber.query.filter_by(email="barber@example.com").first()
    assert barber is not None


def test_signin_barber_account(client):
    # First, create a barber account
    client.post('/', data=dict(
        first_name="Barber",
        last_name="User",
        email="barber@example.com",
        password="password",
        confirm_password="password",
        user_type="barber"
    ), follow_redirects=True)

    # Now, sign into the barber account
    response = client.post('/signin', data=dict(
        email="barber@example.com",
        password="password"
    ), follow_redirects=True)
    assert response.status_code == 200
    assert b"Welcome" in response.data
