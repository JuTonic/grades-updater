import gspread
import locale
from time import sleep
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from bs4 import BeautifulSoup, ResultSet
from google.oauth2.service_account import Credentials
import os
from dotenv import load_dotenv

load_dotenv()

locale.setlocale(locale.LC_ALL, '')

TRIM_BEFORE = 39
CHUNK_SIZE = 3
EXCLUDE_HEADERS = ["ДЗ1", "ДЗ2", "ДЗ3", "ДЗ4", "ДЗ5", "ДЗ6", "ДЗ7", "ДЗ8", "Итог"]
username = os.getenv("USERNAME")
password = os.getenv("PASSWORD")
GOOGLE_TOKEN_PATH = "/app/token/token.json" if os.getenv("GOOGLE_TOKEN_PATH") is None else os.getenv("GOOGLE_TOKEN_PATH")

options = Options()
options.add_argument("--no-sandbox")
options.add_argument("--headless")
options.add_argument("--disable-dev-shm-usage")
options.binary_location = "/usr/bin/firefox-esr"

print("Logging into HSE LMS...")

firefox = webdriver.Firefox(options=options)

firefox.get('https://edu.hse.ru/auth/oidckc/')

firefox.find_element("name", "username").send_keys(username)
firefox.find_element("name", "password").send_keys(password)
firefox.find_element("name", "login").click()

sleep(3)

print("Logged in. Parsing grades...")

firefox.get("https://edu.hse.ru/grade/report/grader/index.php?id=202858")

html = BeautifulSoup(firefox.page_source, "html.parser")

firefox.quit()

exclude_indexes: list[int] = []

_gradesHeaders: list[str] = list(map(lambda h: h.text.strip(), html.find_all("a", {"class": "gradeitemheader"})))

gradesHeaders: list[str] = []

for i in range(len(_gradesHeaders)):
    if _gradesHeaders[i] in EXCLUDE_HEADERS:
        exclude_indexes.append(i)
    else:
        gradesHeaders.append(_gradesHeaders[i])

gradesHeaders = gradesHeaders[TRIM_BEFORE:]

students: ResultSet[BeautifulSoup] = html.findAll("tr", {"class": "userrow"})

studentGrades = {} 

for student in students:
    name = student.find("a", {"class": "username"}).contents[1].strip()
    grades_temp: list[str] = list(map(lambda span: span.contents[0].strip(), student.find_all("span", {"class", "gradevalue"})))[:-1]
    grades: list[str] = []
    for i in range(len(grades_temp)):
        if i not in exclude_indexes:
            grades.append(grades_temp[i])
    grades = list(map(lambda v: None if v == "-" else locale.atof(v.replace(",", ".")), grades))[TRIM_BEFORE:]

    studentGrades[name] = grades

print("Grades parsed. Updating spreadsheets...")

creds = Credentials.from_service_account_file(
    GOOGLE_TOKEN_PATH,
    scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
)

client = gspread.auth.authorize(creds)

spreadsheet = client.open("Эконометрика-2. Ведомость")

for i in [1, 2, 3]:
    group: list[str] = spreadsheet.worksheet(f"Группа {i}").col_values(2)[2:]
    ws = spreadsheet.worksheet(f"test_grades_{i}")
    ws.clear()
    data = [[""] + gradesHeaders]
    for student in group:
        grades = []
        if student in studentGrades.keys():
            grades = studentGrades[student]
        data.append([student] + grades)
    ws.update("A1", data)

print("Done!")
