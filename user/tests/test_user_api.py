import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status

CREATE_USER_URL = reverse('user:create')
TOKEN_URL = reverse('user:token')
ME_URL = reverse('user:me')


@pytest.fixture
def create_user(db):
    def make_user(**kwargs):
        return get_user_model().objects.create_user(**kwargs)
    return make_user


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def auto_login_user(db, api_client):
    user = get_user_model().objects.create_superuser(
        'test@test.com',
        'test123'
    )
    api_client.force_authenticate(user=user)


class TestPublicUserApi():
    """Test the users API (public)"""

    @pytest.mark.django_db
    def test_create_valid_user_successful(self, api_client):
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

    def test_user_exists(self, create_user, api_client):
        """ Test creating user already exists fails"""
        payload = {
            'email': 'test@test.com',
            'password': 'testpass',
            'name': 'Test',
        }
        create_user(**payload)
        res = api_client.post(CREATE_USER_URL, payload)

        assert res.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.django_db
    def test_password_too_short(self, api_client):
        """ Test that the password must be more than 5 characters """
        payload = {
            'email': 'test@test.com',
            'password': 'pw',
            'name': 'Test',
        }
        res = api_client.post(CREATE_USER_URL, payload)
        assert res.status_code == status.HTTP_400_BAD_REQUEST

        user_exists = get_user_model().objects.filter(
            email=payload['email']).exists()
        assert user_exists == False

    def test_create_token_for_user(self, create_user, api_client):
        """Test that a token is created for the user"""
        payload = {'email': 'test@test.com', 'password': 'testpass'}
        create_user(**payload)
        res = api_client.post(TOKEN_URL, payload)

        assert 'token' in res.data
        assert res.status_code == status.HTTP_200_OK

    def test_create_token_invalid_credentials(self, create_user, api_client):
        """Test that token is not created if invalid credentials are given"""
        payload = {'email': 'test@test.com', 'password': 'testpass'}
        create_user(**payload)
        payload = {'email': 'test@test.com', 'password': 'wrong'}
        res = api_client.post(TOKEN_URL, payload)

        assert 'token' not in res.data
        assert res.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.django_db
    def test_create_token_no_user(self, api_client):
        """Test that token is not created if user doens't exist"""
        payload = {'email': 'test@test.com', 'password': 'testpass'}
        res = api_client.post(TOKEN_URL, payload)

        assert 'token' not in res.data
        assert res.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_token_missing_field(self, api_client):
        """Test that email and password are required"""
        res = api_client.post(TOKEN_URL, {'email': 'one', 'password': ''})

        assert 'token' not in res.data
        assert res.status_code == status.HTTP_400_BAD_REQUEST

    def test_retrieve_user_unauthorized(self, api_client):
        """Test that authentication required for users"""
        res = api_client.get(ME_URL)

        assert res.status_code == status.HTTP_401_UNAUTHORIZED


class TestPrivateUserApi():
    """Test the users API (private)"""

    def test_retrieve_profile_success(self, auto_login_user, api_client):
        """Test retrieving profile for logged in user"""
        res = api_client.get(ME_URL)

        assert res.status_code == status.HTTP_200_OK

    def test_post_me_not_allowed(self, api_client):
        """Test that POST is not allowed on the me URL"""
        res = api_client.post(ME_URL, {})

        assert res.status_code == status.HTTP_401_UNAUTHORIZED

    def test_update_user_profile(self, create_user, api_client):
        """Test updating the user profile for authenticated user"""
        create_payload = {
            'email': 'test@test.com',
            'password': 'testpass',
            'name': 'Test',
        }
        user = create_user(**create_payload)
        api_client.force_authenticate(user=user)

        update_payload = {
            'password': 'newpass',
            'name': 'testy test',
        }
        res = api_client.patch(ME_URL, update_payload)

        user.refresh_from_db()

        assert user.name == update_payload['name']
        assert user.check_password(update_payload['password']) == True
        assert res.status_code == status.HTTP_200_OK
