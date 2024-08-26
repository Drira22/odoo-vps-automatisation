#!/bin/bash

docker stop $(docker ps -q)
docker rm $(docker ps -a -q)
docker volume rm $(docker volume ls -q)

# Directories to check
AVAILABLE_DIR="/etc/nginx/sites-available"
ENABLED_DIR="/etc/nginx/sites-enabled"

# Files to keep
KEEP_FILES=("default" "odoo_flask" "odoo_subdomain_template")

# Function to remove unwanted files
cleanup_directory() {
    local DIR=$1
    echo "Cleaning up directory: $DIR"
    for FILE in "$DIR"/*; do
        FILE_NAME=$(basename "$FILE")
        if [[ ! " ${KEEP_FILES[@]} " =~ " ${FILE_NAME} " ]]; then
            echo "Removing $FILE"
            sudo rm "$FILE"
        else
            echo "Keeping $FILE"
        fi
    done
}

# Cleanup both directories
cleanup_directory "$AVAILABLE_DIR"
cleanup_directory "$ENABLED_DIR"

# Restart Nginx
echo "Restarting Nginx"
sudo systemctl restart nginx

echo "Cleanup completed and Nginx restarted."

