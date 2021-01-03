import tempfile
import os
import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from unittest.mock import patch
from PIL import Image


from recipe.models import Recipe, Tag, Ingredient, recipe_image_file_path
from recipe.serializers import RecipeSerializer, RecipeDetailSerializer

RECIPES_URL = reverse('recipe:recipe-list')


def detail_url(recipe_id):
    """ Return recipe URL """
    return reverse('recipe:recipe-detail', args=[recipe_id])


def image_upload_url(recipe_id):
    """ Return URL for recipe image upload """
    return reverse('recipe:recipe-upload-image', args=[recipe_id])


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


def test_recipe_str(create_user):
    """Test the recipe string representation"""
    recipe = Recipe.objects.create(
        user=create_user(),
        title="Steak and mushroom sauce",
        time_minutes=5,
        price=5.00
    )

    assert str(recipe) == recipe.title


@patch('uuid.uuid4')
def test_recipe_file_name_uuid(mock__uuid):
    """ Test that image is saved in the correct location """
    uuid = 'test-uuid'
    mock__uuid.return_value = uuid
    file_path = recipe_image_file_path(None, 'myimage.jpg')

    exp_path = f'uploads/recipe/{uuid}.jpg'
    assert file_path == exp_path


class TestPublicRecipeApi:
    """ Test unauthenticated recipe API access """

    def test_auth_required(self, api_client):
        """ Test that authentication is required """
        res = api_client.get(RECIPES_URL)

        assert res.status_code == status.HTTP_401_UNAUTHORIZED


class TestPrivateRecipeApi:
    """ Test authenticated recipe access """

    def test_retrieve_recipes(self, auto_login_user, api_client):
        """ Test retrieving a list of recipes """

        payload = {
            'title': 'Sample Recipe',
            'time_minutes': 10,
            'price': 5.00
        }

        Recipe.objects.create(user=auto_login_user, **payload)
        Recipe.objects.create(user=auto_login_user, **payload)

        res = api_client.get(RECIPES_URL)
        recipes = Recipe.objects.all().order_by('-id')
        serializer = RecipeSerializer(recipes, many=True)

        assert res.status_code == status.HTTP_200_OK
        assert res.data == serializer.data

    def test_recipes_limited_to_user(self, auto_login_user, api_client):
        """ Test retrieving recipes for user """
        user2 = get_user_model().objects.create_user(
            'other@test.com',
            'testpass'
        )
        payload = {
            'title': 'Sample Recipe',
            'time_minutes': 10,
            'price': 5.00
        }

        Recipe.objects.create(user=auto_login_user, **payload)
        Recipe.objects.create(user=user2, **payload)

        res = api_client.get(RECIPES_URL)

        recipes = Recipe.objects.filter(user=auto_login_user)
        serializer = RecipeSerializer(recipes, many=True)

        assert res.status_code == status.HTTP_200_OK
        assert res.data == serializer.data

    def test_view_recipe_detail(self, auto_login_user, api_client):
        """ Test viewing a recipe detail """
        payload = {
            'title': 'Sample Recipe',
            'time_minutes': 10,
            'price': 5.00
        }

        recipe = Recipe.objects.create(user=auto_login_user, **payload)

        tag = Tag.objects.create(user=auto_login_user, name='Vegan')
        recipe.tags.add(tag)

        ingredient = Ingredient.objects.create(
            user=auto_login_user, name='Kale')
        recipe.ingredients.add(ingredient)

        url = detail_url(recipe.id)
        res = api_client.get(url)

        serializer = RecipeDetailSerializer(recipe)

        assert res.data == serializer.data

    def test_create_basic_recipe(self, auto_login_user, api_client):
        """ Test creating recipe """
        payload = {
            'title': 'Sample Recipe',
            'time_minutes': 10,
            'price': 5.00
        }

        res = api_client.post(RECIPES_URL, payload)
        assert res.status_code == status.HTTP_201_CREATED

        recipe = Recipe.objects.get(id=res.data['id'])

        for key in payload.keys():
            assert payload[key] == getattr(recipe, key)

    def test_create_recipe_with_tags(self, auto_login_user, api_client):
        """ Test creating a recipe with tags """
        tag1 = Tag.objects.create(user=auto_login_user, name='Vegan')
        tag2 = Tag.objects.create(user=auto_login_user, name='Dessert')
        payload = {
            'title': 'Sample Recipe',
            'tags': [tag1.id, tag2.id],
            'time_minutes': 50,
            'price': 20.00
        }

        res = api_client.post(RECIPES_URL, payload)
        assert res.status_code == status.HTTP_201_CREATED

        recipe = Recipe.objects.get(id=res.data['id'])
        tags = recipe.tags.all()

        assert tags.count() == 2
        assert tag1 in tags
        assert tag2 in tags

    def test_create_recipe_with_ingredients(self, auto_login_user, api_client):
        """ Test creating recipe with ingredients """
        ingredient1 = Ingredient.objects.create(
            user=auto_login_user, name='Kale')
        ingredient2 = Ingredient.objects.create(
            user=auto_login_user, name='Mustard')

        payload = {
            'title': 'Sample Recipe',
            'ingredients': [ingredient1.id, ingredient2.id],
            'time_minutes': 50,
            'price': 20.00
        }

        res = api_client.post(RECIPES_URL, payload)
        assert res.status_code == status.HTTP_201_CREATED

        recipe = Recipe.objects.get(id=res.data['id'])
        ingredients = recipe.ingredients.all()

        assert ingredients.count() == 2
        assert ingredient1 in ingredients
        assert ingredient2 in ingredients

    def test_partial_update_recipe(self, auto_login_user, api_client):
        """ Test updating a recipe with patch """
        payload = {
            'title': 'Sample Recipe',
            'time_minutes': 10,
            'price': 5.00
        }

        recipe = Recipe.objects.create(user=auto_login_user, **payload)
        tag = Tag.objects.create(user=auto_login_user, name='Vegan')
        recipe.tags.add(tag)

        new_tag = Tag.objects.create(user=auto_login_user, name='Indian')
        payload = {
            'title': 'Indian Recipe',
            'tags': [new_tag.id]
        }
        url = detail_url(recipe.id)
        api_client.patch(url, payload)

        recipe.refresh_from_db()

        assert recipe.title == payload['title']

        tags = recipe.tags.all()
        assert tags.count() == 1
        assert new_tag in tags

    def test_full_update_recip(self, auto_login_user, api_client):
        """ Test updating a recipe with put """
        payload = {
            'title': 'Sample Recipe',
            'time_minutes': 10,
            'price': 5.00
        }

        recipe = Recipe.objects.create(user=auto_login_user, **payload)
        tag = Tag.objects.create(user=auto_login_user, name='Vegan')
        recipe.tags.add(tag)

        payload = {
            'title': 'Spaghetti',
            'time_minutes': 25,
            'price': 6.00
        }

        url = detail_url(recipe.id)
        api_client.put(url, payload)

        recipe.refresh_from_db()

        assert recipe.title == payload['title']
        assert recipe.time_minutes == payload['time_minutes']
        tags = recipe.tags.all()
        assert tags.count() == 0


class TestRecipeImageUpload:

    def test_upload_image_to_recipe(self, auto_login_user, api_client):
        """ Test uploading an email to recipe """

        payload = {
            'title': 'Sample Recipe',
            'time_minutes': 10,
            'price': 5.00
        }

        recipe = Recipe.objects.create(user=auto_login_user, **payload)
        url = image_upload_url(recipe.id)

        with tempfile.NamedTemporaryFile(suffix='.jpg') as ntf:
            img = Image.new('RGB', (10, 10))
            img.save(ntf, format='JPEG')
            ntf.seek(0)
            res = api_client.post(url, {'image': ntf}, format='multipart')

        recipe.refresh_from_db()

        assert res.status_code == status.HTTP_200_OK
        assert 'image' in res.data
        assert os.path.exists(recipe.image.path) == True

        recipe.image.delete()

    def test_upload_image_bad_request(self, auto_login_user, api_client):
        """ Test upload an invalid image """

        payload = {
            'title': 'Sample Recipe',
            'time_minutes': 10,
            'price': 5.00
        }

        recipe = Recipe.objects.create(user=auto_login_user, **payload)
        url = image_upload_url(recipe.id)
        res = api_client.post(url, {'image': 'notimage'}, format='multipart')

        assert res.status_code == status.HTTP_400_BAD_REQUEST

    def test_filter_recipe_by_tags(self, auto_login_user, api_client):
        """ Test returning recipes with specific tags """
        payload = {
            'title': 'Sample Recipe',
            'time_minutes': 10,
            'price': 5.00
        }

        recipe1 = Recipe.objects.create(user=auto_login_user, **payload)
        recipe2 = Recipe.objects.create(user=auto_login_user, **payload)
        tag1 = Tag.objects.create(user=auto_login_user, name='Vegan')
        tag2 = Tag.objects.create(user=auto_login_user, name='Spicy')
        recipe1.tags.add(tag1)
        recipe2.tags.add(tag2)

        res = api_client.get(RECIPES_URL, {'tags': f'{tag1.id}'})

        serializer1 = RecipeSerializer(recipe1)
        serializer2 = RecipeSerializer(recipe2)

        assert serializer1.data in res.data
        assert serializer2.data not in res.data

    def test_filter_recipes_by_ingredients(self, auto_login_user, api_client):
        """ Test returning recipes with specific ingredients """
        payload = {
            'title': 'Sample Recipe',
            'time_minutes': 10,
            'price': 5.00
        }

        recipe1 = Recipe.objects.create(user=auto_login_user, **payload)
        recipe2 = Recipe.objects.create(user=auto_login_user, **payload)
        ingredient1 = Ingredient.objects.create(
            user=auto_login_user, name='Feta Cheese')
        ingredient2 = Ingredient.objects.create(
            user=auto_login_user, name='Tarama')
        recipe1.ingredients.add(ingredient1)
        recipe2.ingredients.add(ingredient2)

        res = api_client.get(RECIPES_URL, {'ingredients': f'{ingredient1.id}'})

        serializer1 = RecipeSerializer(recipe1)
        serializer2 = RecipeSerializer(recipe2)

        assert serializer1.data in res.data
        assert serializer2.data not in res.data
