FROM python:3.8-alpine

WORKDIR /app


RUN python -m venv venv
COPY requirements.txt requirements.txt
RUN venv/bin/pip install -r requirements.txt

COPY . .


EXPOSE 5000
ENTRYPOINT ["venv/bin/python", "-m", "flask", "run","--host=0.0.0.0"]