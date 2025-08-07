# grades-updater

This repository serves as a reference for anyone looking to develop their own HSE LMS parser. It is not meant to be a 'plug and play' solution.

## What it does

1. Aquires auth token for HSE LMS using the username and password you provided inside `.env` file.
2. Goes to the course page and parses the HTML table with student grades.
3. Inserts it to the google sheets using the token.json.

## Tech Stack

The script uses [selenium](https://www.selenium.dev/) inside docker to simulate a browser session (needed to aquire the auth token) and download the course page, [beautifulsoup4](https://pypi.org/project/beautifulsoup4/) for parsing content of an HTML page and [gspread](https://docs.gspread.org/en/latest/) to interact with google sheets.

## How it was used

Put your hse username and password inside `.env` file:
```bash
USERNAME=[your username]
PASSWORD=[your password]
```

Get a google [api key credential](https://developers.google.com/workspace/guides/create-credentials#api-key) in json format and put it in `token/token.json`. It should look something like:

```json
{
  "type": "service_account",
  "project_id": "your-project-id",
  "private_key_id": "your-private-key-id",
  "private_key": "-----BEGIN PRIVATE KEY-----\nyour-private-key\n-----END PRIVATE KEY-----\n",
  "client_email": "your-client-email@your-client-domain.com",
  "client_id": "your-client-id",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/your-client-cert",
  "universe_domain": "googleapis.com"
}
```

Build the docker image:
```bash
docker build -t update-grades .
```

Run the script (assuming you are in repo folder) mounting the token `folder` and using the `.env` file:
```bash
sudo docker run \
  --volume ./token:/app/token \
  --env-file=.env \
  update-notes
```
