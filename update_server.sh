#!/bin/bash
# Script to reload services on the server

# Reload Nginx
sudo systemctl reload nginx

# Restart Gunicorn
sudo systemctl restart gunicorn

# Restart Celery
sudo systemctl restart celery

# Restart Redis
sudo systemctl restart redis

echo "Services have been updated."
