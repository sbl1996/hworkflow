# ⒽWorkflow

## Features
- Automated and standardized deep learning experiment management 
- Based on GitHub and Google Sheets, accesible for individual and team
- Automatic experiment repeating, results synchronization and error recovery

## Concepts

### Github
- Using repository to manage code and log.
- Every project has a folder in the repo.

### Google Sheet
- Every project has a sheet to record experiment settings and results.

## Authorization

### Github
- The repo access is granted by Github access token 
- Get personal access token: [Creating a personal access token](https://docs.github.com/en/free-pro-team@latest/github/authenticating-to-github/creating-a-personal-access-token)
- In "Select scopes", choose "repo"

### Google Sheet
- Sheets accesses are granted by credentials json file
- A Google Cloud Platform project with the API enabled. To create a project and enable an API, refer to [Create a project and enable the API](https://developers.google.com/workspace/guides/create-project)
- Authorization credentials for a desktop application. To learn how to create credentials for a desktop application, refer to [Create credentials](https://developers.google.com/workspace/guides/create-credentials)
- The detailed steps are listed below:
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

    Training on any workers

### User Workflow
1. Add a row in Sheet
2. Push code to Repo
3. Wait for experiment result

### Worker Workflow
1. Fetch code from Github
2. Training
3. Push result to Sheet and push log to Repo