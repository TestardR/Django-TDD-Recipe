import pytest
from django.contrib.auth import get_user_model

from recipe import models


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


def test_recipe_str(create_user):
    """Test the recipe string representation"""
    recipe = models.Recipe.objects.create(
        user=create_user(),
        title="Steak and mushroom sauce",
        time_minutes=5,
        price=5.00
    )

    assert str(recipe) == recipe.title
