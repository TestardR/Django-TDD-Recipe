import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse


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


@pytest.mark.django_db
def test_new_user_invalid_email():
    """ Test creating a user with no email raises error """
    with pytest.raises(ValueError):
        get_user_model().objects.create_user(None, 'test123')


@pytest.mark.django_db
def test_create_new_superuser():
    """ Test creating a new superuser """
    user = get_user_model().objects.create_superuser(
        'test@test.com',
        'test123'
    )

    assert user.is_superuser == True
    assert user.is_staff == True


