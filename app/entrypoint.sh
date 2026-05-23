#!/bin/sh

if [ "$SERVER_TYPE" = "daphne" ]; then
    echo "Starting Daphne..."
    exec daphne -b 0.0.0.0 -p 8000 messenger.asgi:application
else
    echo "Starting Django runserver..."
    exec python manage.py runserver 0.0.0.0:8000
fi