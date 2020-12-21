import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse


@pytest.fixture
def auto_login_superuser(db, admin_client):
    user = get_user_model().objects.create_superuser(
        'test@test.com',
        'test123'
    )
    admin_client.login(email=user.email,
                       password=user.password)


def test_users_listed(auto_login_superuser, admin_client):
    """ Test that users are listed on user page """
    url = reverse('admin:authentication_user_changelist')
    response = admin_client.get(url)

    assert response.status_code == 200
