#!/bin/sh

# Path to the configurations file
CONFIG_FILE="/consul/configs/configurations.yaml"

# Function to Wait for Consul to be Ready
wait_for_consul() {
  echo "Waiting for Consul to be available at consul:8500..."
  until curl -s http://consul:8500/v1/status/leader >/dev/null; do
    echo "Consul not available yet. Retrying in 5 seconds..."
    sleep 5
  done
  echo "Consul is up and running."
}

# Function to Add Configuration to Consul KV Store
add_configs_to_consul() {
  echo "Adding configurations to Consul KV store from $CONFIG_FILE..."

  # Check if the configuration file exists
  if [ ! -f "$CONFIG_FILE" ]; then
    echo "Configuration file $CONFIG_FILE not found!"
    exit 1
  fi

  # Use yq to parse YAML (ensure yq is installed)
  # yq is a lightweight and portable command-line YAML processor
  # Install yq if not already present
  if ! command -v yq &> /dev/null; then
    echo "yq not found, installing..."
    wget https://github.com/mikefarah/yq/releases/download/v4.34.1/yq_linux_amd64 -O /usr/local/bin/yq
    chmod +x /usr/local/bin/yq
  fi

  # Iterate over each configuration entry
  TOTAL=$(yq e '. | length' "$CONFIG_FILE")
  for i in $(seq 0 $((TOTAL - 1))); do
    KEY=$(yq e ".[$i].key" "$CONFIG_FILE")
    VALUE=$(yq e ".[$i].value" "$CONFIG_FILE")

    echo "Processing key: $KEY"

    # Check if the key already exists
    EXISTING_VALUE=$(curl -s http://consul:8500/v1/kv/$KEY?raw)

    if [ "$EXISTING_VALUE" = "" ]; then
      echo "Configuration key '$KEY' does not exist. Creating..."
      RESPONSE=$(curl --write-out "%{http_code}" --silent --output /dev/null --request PUT \
        --data "$VALUE" \
        http://consul:8500/v1/kv/$KEY)
      
      if [ "$RESPONSE" -eq 200 ]; then
        echo "Configuration '$KEY' added successfully."
      else
        echo "Failed to add configuration '$KEY'. HTTP response code: $RESPONSE"
        exit 1
      fi
    else
      echo "Configuration key '$KEY' already exists. Skipping..."
    fi
  done

  echo "All configurations have been processed."
}

# Execute Functions
wait_for_consul
add_configs_to_consul

echo "Consul initialization completed successfully."
