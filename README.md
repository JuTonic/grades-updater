# grades-updater

This repository serves as a reference for anyone looking to develop their own HSE LMS parser.

## How it used

Put your hse username and password inside `.env` file:
```bash
USERNAME=[your username]
PASSWORD=[your password]
```

Get a google [api key credential](https://developers.google.com/workspace/guides/create-credentials#api-key) in json format and put it in `token/token.json`

Build the docker image:
```bash
docker build -t update-grades .
```

Run the script (assuming you are in repo folder):
```bash
sudo docker run \
  --volume ./token:/app/token \
  --env-file=.env \
  update-notes
```
## What it does

1. Aquires auth token for HSE LMS using the username and password you provided inside `.env` file. It does it via selenium that simulates a firefox browser session (that is why the docker is used).
2. Goes to the course page and parses the HTML table with student grades.
3. Inserts it to the google sheets using the token.json.
