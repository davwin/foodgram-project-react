import json
import os

from django.conf import settings
from django.core.management import BaseCommand
from foods.models import Ingredient

INGREDIENTS_CSV = 'ingredients.csv'
INGREDIENTS_JSON = 'ingredients.json'

data_path = settings.BASE_DIR
path = os.path.join(data_path, INGREDIENTS_JSON)


class Command(BaseCommand):
    help = 'Загрузка ингредиентов в БД из файла'

    def handle(self, *args, **options):
        path = os.path.join(data_path, INGREDIENTS_JSON)
        Ingredient.objects.all().delete()

        with open(path, 'r', encoding='utf-8') as f:
            Ingredient.objects.bulk_create(
                objs=[Ingredient(**x) for x in json.load(f)],
                ignore_conflicts=True
            )
