import json
import os

from django.conf import settings
from django.core.management import BaseCommand
from foods.models import Ingredient, Tag

INGREDIENTS_CSV = 'ingredients.csv'
INGREDIENTS_JSON = 'ingredients.json'
TAGS_JSON = 'tags.json'

data_path = settings.BASE_DIR
path = os.path.join(data_path, INGREDIENTS_JSON)


class Command(BaseCommand):
    help = 'Загрузка ингредиентов в БД из файла'

    def handle(self, *args, **options):
        ingredients_path = os.path.join(data_path, INGREDIENTS_JSON)
        tags_path = os.path.join(data_path, TAGS_JSON)

        def load_model(path, model):
            model.objects.all().delete()

            with open(path, 'r', encoding='utf-8') as f:
                model.objects.bulk_create(
                    objs=[model(**x) for x in json.load(f)],
                    ignore_conflicts=True
                )

        load_model(ingredients_path, Ingredient)
        load_model(tags_path, Tag)
