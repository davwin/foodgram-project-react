import csv

from django.conf import settings
from django.core.management import BaseCommand
from foods.models import Ingredients

TABLES_DICT = {
    Ingredients: 'ingredients.csv',
}


class Command(BaseCommand):
    help = 'Load data from csv files'

    def handle(self, *args, **kwargs):
        for model, base in TABLES_DICT.items():
            with open(
                f'{settings.BASE_DIR}/data/{base}',
                'r', encoding='utf-8'
            ) as csv_file:
                reader = csv.DictReader(csv_file, delimiter=',')
                model.objects.bulk_create(model(**data) for data in reader)

        self.stdout.write(self.style.SUCCESS('Successfully load data'))
