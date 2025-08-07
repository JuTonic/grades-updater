FROM python:3.13-alpine

RUN apk add --no-cache firefox-esr
RUN apk add --no-cache geckodriver

RUN pip install selenium bs4 gspread python-dotenv

COPY ./app /app

WORKDIR /app

CMD ["python", "main.py"]
