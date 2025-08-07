import gspread                                         # For interacting with Google Sheets
import locale                                          # For parsing localized numbers
from time import sleep                                 # For pausing execution
from selenium import webdriver                         # | For simulating the browser session
from selenium.webdriver.common.by import By            # |
from selenium.webdriver.firefox.options import Options # For headless browser config
from bs4 import BeautifulSoup, ResultSet               # For parsing HTML
from google.oauth2.service_account import Credentials  # Google API authentification
import os                                              #
from dotenv import load_dotenv                         # For loading USERNAME and PASSWORD from .env

# Load environment variables (e.g. USERNAME, PASSWORD, GOOGLE_TOKEN_PATH)
load_dotenv()

# Load credentials from environment variables
username = os.getenv("USERNAME")
password = os.getenv("PASSWORD")
GOOGLE_TOKEN_PATH = "/app/token/token.json" if os.getenv("GOOGLE_TOKEN_PATH") is None else os.getenv("GOOGLE_TOKEN_PATH")

# Set locale for parsing localized number formats (e.g., Russian commas)
locale.setlocale(locale.LC_ALL, '')

# Constants
TRIM_BEFORE = 39 # Trim the first 39 columns of grades (last semester grades)
EXCLUDE_HEADERS = ["ДЗ1", "ДЗ2", "ДЗ3", "ДЗ4", "ДЗ5", "ДЗ6", "ДЗ7", "ДЗ8", "Итог"]
LOGIN_SLEEP_SECONDS = 3 # How long should we wait for login to complete
LOGIN_URL = "https://edu.hse.ru/auth/oidckc/"
COURSE_GRADEBOOK_URL = "https://edu.hse.ru/grade/report/grader/index.php?id=202858"
SPREADSHEET_NAME = "Эконометрика-2. Ведомость"

# Configure Firefox for headless execution in Docker
options = Options()
options.add_argument("--no-sandbox")
options.add_argument("--headless")
options.add_argument("--disable-dev-shm-usage")
options.binary_location = "/usr/bin/firefox-esr" # Headless-compatible Firefox binary

# Start Selenium WebDriver
firefox = webdriver.Firefox(options=options)

print("Logging into HSE LMS...")

# Navigate to the LMS login page
firefox.get(LOGIN_URL)

# Fill in login form with username and password
firefox.find_element("name", "username").send_keys(username)
firefox.find_element("name", "password").send_keys(password)
firefox.find_element("name", "login").click()

# Wait for login to complete
sleep(LOGIN_SLEEP_SECONDS)

print("Logged in. Parsing grades...")

# Go to the gradebook page
firefox.get(COURSE_GRADEBOOK_URL)

# Parse the page content using BeautifulSoup
html = BeautifulSoup(firefox.page_source, "html.parser")

# Close the browser as it is no longer needed
firefox.quit()

# Identify which grade columns to exclude based on their headers
exclude_indexes: list[int] = []
_gradesHeaders: list[str] = list(map(lambda h: h.text.strip(), html.find_all("a", {"class": "gradeitemheader"}))) # Some python magic

gradesHeaders: list[str] = []

# Populate exclude_indexes and cleaned-up gradesHeaders
for i in range(len(_gradesHeaders)):
    if _gradesHeaders[i] in EXCLUDE_HEADERS:
        exclude_indexes.append(i)
    else:
        gradesHeaders.append(_gradesHeaders[i])

# Trim unwanted leading columns
gradesHeaders = gradesHeaders[TRIM_BEFORE:]

# Extract student rows from the grade table
students: ResultSet[BeautifulSoup] = html.findAll("tr", {"class": "userrow"})

# Dictionary to hold student names and their cleaned grade values
studentGrades = {} 

for student in students:
    # Extract full student name
    name = student.find("a", {"class": "username"}).contents[1].strip()
    # Extract raw grade strings for the student
    grades_temp: list[str] = list(map(lambda span: span.contents[0].strip(), student.find_all("span", {"class", "gradevalue"})))[:-1]
    grades: list[str] = [] # Remove the last (summary) grade
    for i in range(len(grades_temp)):
        # Exclude grades by index (based on headers)
        if i not in exclude_indexes:
            grades.append(grades_temp[i])
    
    # Convert grades to floats where possible, treat "-" as None
    grades = list(map(lambda v: None if v == "-" else locale.atof(v.replace(",", ".")), grades))[TRIM_BEFORE:] # Trim leading columns

    # Store in dictionary
    studentGrades[name] = grades

print("Grades parsed. Updating spreadsheets...")

# Authenticate with Google API using service account
creds = Credentials.from_service_account_file(
    GOOGLE_TOKEN_PATH,
    scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
)

# Create gspread client
client = gspread.auth.authorize(creds)

# Open the spreadsheet by name
spreadsheet = client.open(SPREADSHEET_NAME)

# Loop over 3 groups of students and update their respective worksheets
for i in [1, 2, 3]:
    # Get the list of student names from column B of the group sheet
    group: list[str] = spreadsheet.worksheet(f"Группа {i}").col_values(2)[2:]

    # Target worksheet to write grades into
    ws = spreadsheet.worksheet(f"test_grades_{i}")
    ws.clear()

    # First row: colu`mn headers
    data = [[""] + gradesHeaders]

    # For each student, append their grades
    for student in group:
        grades = []
        if student in studentGrades.keys():
            grades = studentGrades[student]
        data.append([student] + grades)

    # Upload the updated data
    ws.update("A1", data)

print("Done!")
