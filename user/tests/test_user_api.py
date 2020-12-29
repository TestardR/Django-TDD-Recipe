import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status

CREATE_USER_URL = reverse('user:create')


@pytest.fixture
def create_user(db):
    def make_user(**kwargs):
        return get_user_model().objects.create_user(**kwargs)
    return make_user


@pytest.fixture
def api_client():
    return APIClient()


@pytest.mark.django_db
def test_create_valid_user_successful(api_client):
    """ Test creating user with valid payload is successful """
    payload = {
        'email': 'test@test.py',
        'password': 'testpass',
        'name': 'testname'
    }
    res = api_client.post(CREATE_USER_URL, payload)
    assert res.status_code == status.HTTP_201_CREATED

    user = get_user_model().objects.get(**res.data)
    assert user.check_password(payload['password']) == True
    assert 'password' not in res.data


@pytest.mark.django_db
def test_user_exists(create_user, api_client):
    """ Test creating user already exists fails"""
    payload = {
        'email': 'test@test.com',
        'password': 'testpass',
    }
    create_user(**payload)
    res = api_client.post(CREATE_USER_URL, payload)

    assert res.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_password_too_short(api_client):
    """ Test that the password must be more than 5 characters """
    payload = {
        'email': 'test@test.com',
        'password': 'pw',
    }
    res = api_client.post(CREATE_USER_URL, payload)
    assert res.status_code == status.HTTP_400_BAD_REQUEST

    user_exists = get_user_model().objects.filter(
        email=payload['email']).exists()
    assert user_exists == False
