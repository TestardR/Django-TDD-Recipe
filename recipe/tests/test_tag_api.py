import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

from recipe import models
from recipe.models import Tag
from recipe.serializers import TagSerializer

TAGS_URL = reverse('recipe:tag-list')


@pytest.fixture
def create_user(db):
    def make_user():
        payload = {
            'email': 'test@test.py',
            'password': 'testpass',
            'name': 'testname'
        }
        return get_user_model().objects.create_user(**payload)
    return make_user


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def auto_login_user(db, api_client):
    user = get_user_model().objects.create_user(
        'test@test.com',
        'test123'
    )
    api_client.force_authenticate(user=user)
    return user


def test_tag_str(create_user):
    """Test the tag string representation"""
    tag = models.Tag.objects.create(
        user=create_user(),
        name='Vegan'
    )

    assert str(tag) == tag.name


class TestPublicTagsApi:
    """Test the publicly available tags API"""

    def test_login_required(self, api_client):
        """Test that login required for retrieving tags"""
        res = api_client.get(TAGS_URL)

        assert res.status_code == status.HTTP_401_UNAUTHORIZED


class PrivateTagsApiTests:
    """Test the authorized user tags API"""

    def test_retrieve_tags(self, auto_login_user, apli_client):
        """Test retrieving tags"""
        user = auto_login_user()

        Tag.objects.create(user=user, name='Vegan')
        Tag.objects.create(user=user, name='Dessert')

        res = apli_client.get(TAGS_URL)

        tags = Tag.objects.all().order_by('-name')
        serializer = TagSerializer(tags, many=True)

        assert res.status_code == status.HTTP_200_OK
        assert res.data == serializer.data

    def test_tags_limited_to_user(self, auto_login_user, apli_client):
        """Test that tags returned are for authenticated user"""
        user = auto_login_user()
        user2 = get_user_model().objects.create_user(
            'other@test.com',
            'testpass'
        )
        Tag.objects.create(user=user2, name='Fruity')
        tag = Tag.objects.create(user=user, name='Comfort Food')

        res = apli_client.get(TAGS_URL)

        assert res.status_code == status.HTTP_200_OK
        assert len(res.data) == 1
        assert res.data[0]['name'] == tag.name

    def test_create_tag_successful(self, apli_client):
        """Test creating a new tag"""
        payload = {'name': 'Simple'}
        apli_client.post(TAGS_URL, payload)

        exists = Tag.objects.filter(
            user=self.user,
            name=payload['name']
        ).exists()

        assert exists == True

    def test_create_tag_invalid(self, apli_client):
        """Test creating a new tag with invalid payload"""
        payload = {'name': ''}
        res = apli_client.post(TAGS_URL, payload)

        assert res.status_code == status.HTTP_400_BAD_REQUEST