FROM python:3.11.0-alpine

MAINTAINER "Rodolfo Gonzalez" <rodolfo.gonzalez@gmail.com>
ENV container docker

WORKDIR /usr/src/app

COPY src/certbot/requirements.txt .

RUN apk add certbot

RUN python -m pip install --upgrade pip

RUN pip3 install --no-cache-dir -r requirements.txt

COPY lib/python/config.py .

COPY src/certbot/src/certbotp.py .
COPY src/certbot/src/app.py .

CMD ["python", "./app.py"]