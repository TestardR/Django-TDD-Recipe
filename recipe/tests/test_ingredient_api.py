import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

from recipe import models
from recipe.models import Ingredient
from recipe.serializers import IngredientSerializer

INGREDIENTS_URL = reverse('recipe:ingredient-list')


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


def test_ingredient_str(create_user):
    """Test the ingredient string representation"""
    ingredient = models.Ingredient.objects.create(
        user=create_user(),
        name='Cucumber'
    )

    assert str(ingredient) == ingredient.name


class TestPublicIngredientsApi:
    """Test the publicly available ingredients API"""

    def test_login_required(self, api_client):
        """Test that login required for retrieving ingredients"""
        res = api_client.get(INGREDIENTS_URL)

        assert res.status_code == status.HTTP_401_UNAUTHORIZED


class TestPrivateIngredientsApi:
    """Test the private ingredients API"""

    def test_retrieve_ingredient_list(self, auto_login_user, api_client):
        """Test retrieving ingredients"""
        user = auto_login_user

        Ingredient.objects.create(user=user, name='Kale')
        Ingredient.objects.create(user=user, name='Salt')

        res = api_client.get(INGREDIENTS_URL)

        ingredients = Ingredient.objects.all().order_by('-name')
        serializer = IngredientSerializer(ingredients, many=True)

        assert res.status_code == status.HTTP_200_OK
        assert res.data == serializer.data

    def test_ingredients_limited_to_user(self, auto_login_user, api_client):
        """Test that ingredients returned are for authenticated user"""
        user2 = get_user_model().objects.create_user(
            'other@test.com',
            'testpass'
        )
        Ingredient.objects.create(user=user2, name='Vinegar')
        ingredient = Ingredient.objects.create(
            user=auto_login_user, name='Pepper')

        res = api_client.get(INGREDIENTS_URL)

        assert res.status_code == status.HTTP_200_OK
        assert len(res.data) == 1
        assert res.data[0]['name'] == ingredient.name

    def test_create_ingredient_successful(self, auto_login_user, api_client):
        """Test creating a new tag"""
        payload = {'name': 'Carrot'}
        api_client.post(INGREDIENTS_URL, payload)

        exists = Ingredient.objects.filter(
            user=auto_login_user,
            name=payload['name']
        ).exists()

        assert exists == True

    def test_create_ingredient_invalid(self, auto_login_user, api_client):
        """Test creating a new tag with invalid payload"""
        payload = {'name': ''}
        res = api_client.post(INGREDIENTS_URL, payload)

        assert res.status_code == status.HTTP_400_BAD_REQUEST
