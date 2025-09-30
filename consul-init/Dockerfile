FROM alpine:3.18

# Install necessary packages
RUN apk add --no-cache curl bash wget

# Copy the initialization script and configurations into the container
COPY init-consul.sh /usr/local/bin/init-consul.sh
COPY configs/configurations.yaml /consul/configs/configurations.yaml

# Make the script executable
RUN chmod +x /usr/local/bin/init-consul.sh

# Set the entrypoint to the initialization script
ENTRYPOINT ["/bin/bash", "/usr/local/bin/init-consul.sh"]