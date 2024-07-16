#!/bin/bash


#######################port check############################################

# Function to check if a port is in use
function check_port {
    local port=$1
    for p in "${ports_list[@]}"; do
        if [[ "$p" == "$port" ]]; then
            return 0  
        fi
    done
    return 1  
}

# Initialize array to store ports
ports_list=()

# Read ports into the array using process substitution
while IFS= read -r port; do
    ports_list+=("$port")
done < <(docker ps --format "{{.Ports}}" | grep -o '0\.0\.0\.0:[0-9]\+' | awk -F':' '{print $2}')

echo "Mapped ports on the host:"
echo "${ports_list[@]}"

# Prompt user for Odoo port and check if it's in use
while true; do
    echo 'Enter the port number for Odoo: '
    read ODOO_PORT
    if check_port "$ODOO_PORT"; then
        echo "Port $ODOO_PORT is already in use."
    else
        echo "Port $ODOO_PORT is not in use. Okay!"
        break
    fi
done

##############################################################################################""""


# Assign the variables
echo 'Saisir la version d odoo: '
read odoo_version
echo 'Saisir la version de postgres: '
read postgres_version

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

#######################odoo version check############################################
# odoo allowed versions 
odoo_versions=("16.0" "15.0" "14.0" "13.0" "12.0" "11.0" "10.0" "9.0" "8.0" "7.0" "6.1" "6.0" "5.0" "4.0" "3.0" "2.0" "1.0")
# Validate the odoo_version
if contains "$odoo_version" "${odoo_versions[@]}"; then
  echo "Odoo version $odoo_version is valid."
else
  echo "No odoo version mentionned. Defaulting to 'latest'."
  odoo_version="latest"
fi

#######################postgres version check############################################
# postgres allowed versions 
postgres_versions=("15" "14" "13" "12" "11" "10" "9.6" "9.5" "9.4" "9.3" "alpine" "13-alpine" "12-alpine")
# Validate the postgres_version
if contains "$postgres_version" "${postgres_versions[@]}"; then
  echo "Postgresql version $postgres_version is valid."
else
  echo "No Postgresql version mentionned is not valid. Defaulting to 'latest'."
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

#wait until the final initialization of the odoo conatiner and load of db
log_message="HTTP service (werkzeug) running"
until docker logs $container_name 2>&1 | grep -q "$log_message"; do
  sleep 1
done

#copy the files of firestore in the correspandant directory 
docker exec -it $container_name cp -r ./tmp /var/lib/odoo/.local/share/Odoo/filestore





