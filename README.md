# SpreadTalk

## Thank you for cloning SpreadTalk's repository! This README will walk you through on how to set up and use the application

## Stack

- Backend language: Python,
- Web framework: Django,
- ASGI server: Daphne,
- Channeling: channels,
- UI: Vanilla HTML / JS / CSS.

## Setting up

**Here are the steps to set up the application. You need Python for this guide**

### Clone the repo and go to it's root folder

```bash
cd messenger # or other name
```

### Create a virtual enviroment

```bash
python3 -m venv .venv # change .venv to your name is needed; .venv name is recommended
```

### Download required packages

```bash
pip install -r requirements.txt
```

### (if using a new db) Apply migrations

```bash
python manage.py makemigrations # optional; not recommended to run
python manage.py migrate
```

**You're done with the setup! Now you can proceed to startup guide.**

## Startup

**Currently, there is 1 way to start the application:**

### Run natively:

- Enter virtual enviroment:
```bash
source .venv/bin/activate
```
Or if on windows:
```pwsh
.venv/Scripts/Activate # might be incorrect I haven't used w-os for a while
```

- Run the app:
```bash
python manage.py runserver # or via daphne
```

**The app should show it is running a developement (!!!) server and 0 issues.**