FROM python:3.9

WORKDIR /app
COPY . /app

RUN pip install  -r requirements.txt

EXPOSE 7860


CMD ["gunicorn", "-b", "0.0.0.0:7860", "main:app"]