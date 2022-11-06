# praktikum_new_diplom
178.154.204.59
login: admin@admin.ru
password: twj10mv


![foodgram_workflow](https://github.com/davwin/foodgram-project-react/actions/workflows/foodgram_workflow.yml/badge.svg)

# Проект Foodgram
Проект Foodgram позволяет пользователем сайта пубиликовать рецепты с различными ингредиентами. Выбирать избранные рецепты, а так же скачивать корзину покупок. 

У каждого рецепта есть набор ингредиентов и тэгов. По тэгам пожно фильтровать.

## Какие технологии и пакеты использовались:

* requests==2.26.0
* djoser
* django-colorfield
* python-dotenv
* pytest==6.2.4
* pytest-django==4.4.0
* pytest-pythonpath==0.7.3
* asgiref==3.2.10
* Django==2.2.16
* django-filter==2.4.0
* djangorestframework==3.12.4
* djangorestframework-simplejwt==4.8.0
* django-rest-knox
* drf-extra-fields
* gunicorn==20.0.4
* psycopg2-binary==2.8.6
* PyJWT==2.1.0
* pytz==2020.1
* sqlparse==0.3.1 



## Шаблон наполнения env-файла:

DB_ENGINE=django.db.backends.postgresql # указываем, что работаем с postgresql
DB_NAME=postgres # имя базы данных
POSTGRES_USER=postgres # логин для подключения к базе данных
POSTGRES_PASSWORD=postgres # пароль для подключения к БД (установите свой)
DB_HOST=db # название сервиса (контейнера)
DB_PORT=5432 # порт для подключения к БД

## Заполнить БД:
# Импортировать данные из csv файла:

<pre><code>cd backend</code></pre>
<pre><code>cd foodgram</code></pre>
<pre><code>python manage.py import_data</code></pre>

# Заполнить .json файлом:

Через консоль перейдите к проекту.
Зайдите в директорию с файлом manage.py.
Экспортируйте данные в файл.
python manage.py dumpdata > dump.json
# Данные сохранятся в dump.json 
Копируйте файл dump.json с локального компьютера на сервер. Для такой задачи есть утилита scp (от англ. secure copy — «защищённая копия»). Она копирует файлы на сервер по протоколу SSH. Выполните команду:
# scp my_file username@host:<путь-на-сервере>

# Укажите IP своего сервера и путь до своей домашней директории на сервере
scp dump.json praktikum@84.201.161.196:/home/имя_пользователя/.../папка_проекта_с_manage.py/ 
После выполнения этой команды файл dump.json появится в директории проекта на вашем сервере. Подключитесь к серверу и убедитесь в этом.
Работа на локальном компьютере завершена, продолжайте работать уже на сервере: выполните команды для переноса данных с SQLite на PostgreSQL:
# Закинуть dump.json на сервер через scp и выполнить там

python3 manage.py shell  
# выполнить в открывшемся терминале:
>>> from django.contrib.contenttypes.models import ContentType
>>> ContentType.objects.all().delete()
>>> quit()

python manage.py loaddata dump.json 

## Примеры работы API в ReDoc: http://localhost/redoc/