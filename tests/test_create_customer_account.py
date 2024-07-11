import os
import pytest
from app import app, db
from app import User, Customer


@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    client = app.test_client()

    with app.app_context():
        db.create_all()
        yield client
        db.drop_all()


def test_create_customer_account(client):
    response = client.post('/', data=dict(
        first_name="Customer",
        last_name="User",
        email="customer@example.com",
        password="password",
        confirm_password="password",
        user_type="customer"
    ), follow_redirects=True)
    assert response.status_code == 200
    assert b"Account created successfully" in response.data

    customer = Customer.query.filter_by(email="customer@example.com").first()
    assert customer is not None


def test_signin_customer_account(client):
    # First, create a customer account
    client.post('/', data=dict(
        first_name="Customer",
        last_name="User",
        email="customer@example.com",
        password="password",
        confirm_password="password",
        user_type="customer"
    ), follow_redirects=True)

    # Now, sign in to the customer account
    response = client.post('/signin', data=dict(
        email="customer@example.com",
        password="password"
    ), follow_redirects=True)
    assert response.status_code == 200
    assert b"Welcome" in response.data
