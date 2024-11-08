# Use the official Python image as a base
FROM python:3.9-slim-buster

# Install necessary packages and dependencies
RUN apt-get update && apt-get install -y \
    wget \
    unzip \
    gnupg \
    apt-transport-https \
    libglib2.0-0 \
    libgconf-2-4 \
    libxss1 \
    libappindicator1 \
    libindicator7 \
    libnss3 \
    libatk-bridge2.0-0 \
    libgtk-3-0 \
    fonts-liberation \
    libappindicator3-1 \
    xdg-utils \
    libgbm1 \
    libasound2 \
    && rm -rf /var/lib/apt/lists/*

# Set JAVA_HOME environment variable
ENV JAVA_HOME=/usr/local/java

# Update PATH to include Java binaries
ENV PATH=$JAVA_HOME/bin:$PATH

# Copy and extract JDK
COPY jdk/OpenJDK8U-jdk_x64_linux_hotspot_8u422b05.tar.gz /tmp/jdk.tar.gz
RUN mkdir -p /usr/local/java \
    && tar -xzf /tmp/jdk.tar.gz -C /usr/local/java --strip-components=1 \
    && rm /tmp/jdk.tar.gz

# Verify Java installation
RUN java -version

# Add Google Chrome's official GPG key and repository
RUN wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list

# Install Google Chrome
RUN apt-get update && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# Verify Google Chrome installation
RUN google-chrome --version

# Copy Chromedriver and set permissions
COPY chrome/chromedriver-linux64.zip /tmp/
RUN unzip /tmp/chromedriver-linux64.zip -d /tmp/ \
    && mv /tmp/chromedriver-linux64/chromedriver /usr/local/bin/chromedriver \
    && chmod +x /usr/local/bin/chromedriver \
    && rm -rf /tmp/chromedriver-linux64 /tmp/chromedriver-linux64.zip

# Create a symbolic link for browsermob-proxy
RUN ln -s /app/browsermob-proxy-2.1.4-bin/browsermob-proxy-2.1.4/bin/browsermob-proxy /usr/local/bin/browsermob-proxy

# Set the working directory
WORKDIR /app

COPY requirements.txt .
# Install Python dependencies
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy the mcCrawler source code
COPY src/ /app
COPY environment/ ./environment/

# Ensure execution permissions for browsermob-proxy
RUN chmod +x /app/browsermob-proxy-2.1.4-bin/browsermob-proxy-2.1.4/bin/browsermob-proxy

# Expose necessary ports (if applicable)
EXPOSE 8080

# Define environment variable for Browsermob-Proxy path
ENV BROWSERMOB_PROXY_PATH=/app/browsermob-proxy-2.1.4-bin/browsermob-proxy-2.1.4/bin/browsermob-proxy

# Define the entry point or command
CMD ["python", "urlCrawler.py"]
