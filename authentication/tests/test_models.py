import pytest
from django.contrib.auth import get_user_model


@pytest.mark.django_db
def test_create_user_with_email_successful():
    """ Test creating a new user with an email is sucessfull """
    email = 'test@test.com'
    password = '123456'
    user = get_user_model().objects.create_user(
        email=email,
        password=password
    )

    assert get_user_model().objects.count() == 1
    assert user.email == email
    assert user.check_password(password)

@pytest.mark.django_db
def test_new_user_email_normalized():
    """ Test the email for a new user is normalized """
    email = 'test@TEST.COM'
    user = get_user_model().objects.create_user(email, 'test123')

    assert user.email == email.lower()