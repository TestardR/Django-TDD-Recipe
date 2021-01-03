import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

from recipe import models
from recipe.models import Tag, Recipe
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


class TestPrivateTagsApi:
    """Test the authorized user tags API"""

    def test_retrieve_tags(self, auto_login_user, api_client):
        """Test retrieving tags"""

        Tag.objects.create(user=auto_login_user, name='Vegan')
        Tag.objects.create(user=auto_login_user, name='Dessert')

        res = api_client.get(TAGS_URL)

        tags = Tag.objects.all().order_by('-name')
        serializer = TagSerializer(tags, many=True)

        assert res.status_code == status.HTTP_200_OK
        assert res.data == serializer.data

    def test_tags_limited_to_user(self, auto_login_user, api_client):
        """Test that tags returned are for authenticated user"""
        user2 = get_user_model().objects.create_user(
            'other@test.com',
            'testpass'
        )
        Tag.objects.create(user=user2, name='Fruity')
        tag = Tag.objects.create(user=auto_login_user, name='Comfort Food')

        res = api_client.get(TAGS_URL)

        assert res.status_code == status.HTTP_200_OK
        assert len(res.data) == 1
        assert res.data[0]['name'] == tag.name

    def test_create_tag_successful(self, auto_login_user, api_client):
        """Test creating a new tag"""
        payload = {'name': 'Simple'}
        api_client.post(TAGS_URL, payload)

        exists = Tag.objects.filter(
            user=auto_login_user,
            name=payload['name']
        ).exists()

        assert exists == True

    def test_create_tag_invalid(self, auto_login_user, api_client):
        """Test creating a new tag with invalid payload"""
        payload = {'name': ''}
        res = api_client.post(TAGS_URL, payload)

        assert res.status_code == status.HTTP_400_BAD_REQUEST

    def test_retrieve_tags_assigned_to_recipes(self, auto_login_user, api_client):
        """ Test filtering tags by those assigned to recipes """
        tag1 = Tag.objects.create(user=auto_login_user, name='Breakfast')
        tag2 = Tag.objects.create(user=auto_login_user, name='Lunch')

        payload = {
            'title': 'Sample Recipe',
            'time_minutes': 10,
            'price': 5.00
        }

        recipe = Recipe.objects.create(user=auto_login_user, **payload)
        recipe.tags.add(tag1)

        res = api_client.get(TAGS_URL, {'assigned_only': 1})
        serializer1 = TagSerializer(tag1)
        serializer2 = TagSerializer(tag2)

        assert serializer1.data in res.data
        assert serializer2.data not in res.data

    def test_retrieve_tags_assigned_unique(self,  auto_login_user, api_client):
        """ Test filtering tags by assigned returns unique items """
        tag1 = Tag.objects.create(user=auto_login_user, name='Breakfast')
        Tag.objects.create(user=auto_login_user, name='Lunch')

        payload = {
            'title': 'Sample Recipe',
            'time_minutes': 10,
            'price': 5.00
        }

        recipe1 = Recipe.objects.create(user=auto_login_user, **payload)
        recipe1.tags.add(tag1)
        recipe2 = Recipe.objects.create(user=auto_login_user, **payload)
        recipe2.tags.add(tag1)

        res = api_client.get(TAGS_URL, {'assigned_only': 1})

        assert len(res.data) == 1
