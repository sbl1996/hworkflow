# ⒽWorkflow

## Concepts

### Github
- Create a Github repository to manage code and log.
- Every project has a folder in the repo.

### Google Sheet
- Every project has a sheet to record experiment settings and results.

## Authorization

### Github
- The repo access is granted by Github access token 
- Get personal access token: [Creating a personal access token](https://docs.github.com/en/free-pro-team@latest/github/authenticating-to-github/creating-a-personal-access-token)

### Google Sheet
- Sheets accesses are granted by credentials json file
- Check this [guide](https://developers.google.com/sheets/api/quickstart/python#step_1_turn_on_the) for reference
- The steps are listed below:
    - Create a GCP Project
    - Enable Google Sheets API in Dashboard of APIs and services
    - Configure OAuth consent screen of APIs and services (External is OK)
    - Add your google account to Test users
    - Create a new OAuth client ID with type Desktop app in Credentials
    - Download in OAuth 2.0 Client IDs
    - You got the credentials json file 
- At the first time of use, you need to get authorization code from a url. Then the auth information will be save into a token file and auth will be skipped next time.

## Design

### Components

- 1 Repo

    Github repository for code and log

- 1 Sheet

    Google Sheet for hyperparameters and results

- N Worker

    Google Colab for training

### User Workflow
1. Add a row in Sheet
2. Push code to Repo

### Worker Workflow

1. Worker fetch pending task (code) from Sheet
2. Worker complete training
3. Worker push result to Sheet, log to Repo
4. Repeat from 1