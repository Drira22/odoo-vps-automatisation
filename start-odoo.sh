#!/bin/bash

# Ensure the script is run with two arguments
if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <odoo_version> <postgres_version>"
    
fi

# Assign arguments to variables
odoo_version=$1
postgres_version=$2

# Function to check if a port is in use
function check_port {
    local port=$1
    local used_ports
    used_ports=$(docker ps --format "{{.Ports}}" | grep -o '0\.0\.0\.0:[0-9]\+' | awk -F':' '{print $2}')
    for p in $used_ports; do
        if [[ "$p" == "$port" ]]; then
            return 0
        fi
    done
    return 1
}

# Find the first available port starting from 8069
ODOO_PORT=8070
while check_port "$ODOO_PORT"; do
    ((ODOO_PORT++))
done

echo "Using Odoo port: $ODOO_PORT"

# Function to check if a value is in an array
function contains() {
    local value="$1"
    shift
    for v in "$@"; do
        if [[ "$v" == "$value" ]]; then
            return 0
        fi
    done
    return 1
}

# Allowed Odoo versions
odoo_versions=("16.0" "15.0" "14.0" "13.0" "12.0" "11.0" "10.0" "9.0" "8.0" "7.0" "6.1" "6.0" "5.0" "4.0" "3.0" "2.0" "1.0")
# Validate the Odoo version
if contains "$odoo_version" "${odoo_versions[@]}"; then
    echo "Odoo version $odoo_version is valid."
else
    echo "Odoo version $odoo_version is not valid. Defaulting to 'latest'."
    odoo_version="latest"
fi

# Allowed Postgres versions
postgres_versions=("15" "14" "13" "12" "11" "10" "9.6" "9.5" "9.4" "9.3" "alpine" "13-alpine" "12-alpine")
# Validate the Postgres version
if contains "$postgres_version" "${postgres_versions[@]}"; then
    echo "Postgres version $postgres_version is valid."
else
    echo "Postgres version $postgres_version is not valid. Defaulting to 'latest'."
    postgres_version="latest"
fi

# Determine the container name based on the port
container_name="odoo-${ODOO_PORT}"

# Export the variables so they are available to Docker Compose
export ODOO_PORT
export odoo_version
export postgres_version
export container_name

# Run Docker Compose with the updated environment variables
sed "s/ODOO_PORT_TEMPLATE/$ODOO_PORT/g; s/CONTAINER_NAME_TEMPLATE/$container_name/g" docker-compose.yml.template > docker-compose.yml
docker-compose -p $container_name up -d

# Wait until the final initialization of the Odoo container and load of DB
log_message="HTTP service (werkzeug) running"
until docker logs $container_name 2>&1 | grep -q "$log_message"; do
    sleep 1
done

# Copy the files of filestore to the corresponding directory
docker exec -it $container_name cp -r ./tmp /var/lib/odoo/.local/share/Odoo/filestore

# Create a file to signal completion
touch /tmp/odoo_ready_$ODOO_PORT
