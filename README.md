# SpreadTalk

## Thank you for cloning SpreadTalk's repository! This README will walk you through on how to set up and use the application

## Stack

- Backend language: Python 3.12 / 3.13,
- Web framework: Django 6,
- ASGI server: Daphne 4,
- Channeling: channels,
- UI: Vanilla HTML / JS / CSS (latest).

## Setting up

**Here are the steps to set up the application. You need Python for this guide.**

1. Clone the repo and go to it's root folder

```bash
cd SpreadTalk # or other name
```

2. Create a virtual enviroment

```bash
python3 -m venv .venv # change .venv to your name is needed; .venv name is recommended
```

3. Enter the virtual environment:

- On Linux:
```bash
source .venv/bin/activate
```

- On Windows (Powershell / cmd):
```pwsh
.venv/Scripts/Activate # might be incorrect; haven't used Windows for a while
```

4. Download required packages

```bash
pip install -r app/requirements.txt
```

5. Clone .env.example to .env

```bash
cp .env.example .env
```

6. (if using a new db) Apply migrations

```bash
python app/manage.py makemigrations # optional; not recommended to run
python app/manage.py migrate
```

**You're done with the setup! Now you can proceed to startup guide.**

## Startup

**Currently, there are 2 ways to start the application:**

### Option 1: Run natively

1. Enter the virtual environment:

- On Linux:
```bash
source .venv/bin/activate
```

- On Windows (Powershell / cmd):
```pwsh
.venv/Scripts/Activate # might be incorrect; haven't used Windows for a while
```

2. Run the app:
```bash
python app/manage.py runserver # or python3
# or via Daphne (for prod!): daphne -b 0.0.0.0 -p 8000 messenger.asgi:application
```

### Option 2: Docker Compose

**(make sure you have Docker installed, for older versions you may also need to manually install docker-compose package)**

1. Run via Docker Compose:

```bash
docker compose up # or try docker-compose
```

## The app should now start properly.

# User manual

### Backend

**The main backend controller is the .env file. It stores the primary project configurations, such as:**

- **DEBUG**: controls if debug mode is on or off. for small hosts, turning it on (DEBUG=True) is recommended for stability. Otherwise, set it as False: will require configuring SSL keys (advanced).
- **LOG_LEVEL_MAIN**: controls the log level of project's code, this does not include package logs. For regular usage, WARNING is recommended.
- **LOG_LEVEL_SEC**: controls the log level of project packages such as Django, Daphne etc. WARNING is recommended for regular usage.

### Frontend

**Frontend is usually controlled by editing the stylesheets (.css), markup (.html) and Javascript (.js). The site requires Javascript at all times for the frontend to be usable.**