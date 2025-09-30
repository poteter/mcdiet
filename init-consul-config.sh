#!/bin/bash

# Stop and remove the existing consul-init container if it exists
docker-compose down consul-init
docker-compose rm -f consul-init

# Build the consul-init container
docker-compose build consul-init

# Run the consul-init container
docker-compose up -d consul-init

# Remove the consul-init container after it exits
docker-compose down consul-init
docker-compose rm -f consul-init

echo "Consul configurations successfully initialized/updated."
