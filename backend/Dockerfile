# Очень прошу помочь, т.к. наставников больше, фактически, нет.
# Не работает запрос к бэкенду, выдаёт 405 ошибку, но в постмане
# работало. Насколько я понял, ошибка в wsgi файле, но как её поправить
# найти не могу.

FROM python:3.7-slim

WORKDIR /app

COPY requirements.txt ./

RUN pip3 install -r ./requirements.txt --no-cache-dir

COPY . .


CMD gunicorn foodgram.wsgi:application --bind 0.0.0.0:8000