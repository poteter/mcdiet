# Use the official Python image
FROM python:3.9-slim-buster

# Install Java (OpenJDK 11), wget, unzip, gnupg, curl, and xvfb
RUN apt-get update && apt-get install -y \
    openjdk-11-jdk \
    wget \
    unzip \
    gnupg \
    curl \
    xvfb \
    --no-install-recommends

# Install Google Chrome
RUN curl -sSL https://dl.google.com/linux/linux_signing_key.pub | apt-key add - && \
    echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" \
    > /etc/apt/sources.list.d/google.list && \
    apt-get update && apt-get install -y google-chrome-stable

# Install ChromeDriver
RUN CHROME_VERSION=$(google-chrome --version | grep -oE '[0-9.]+') && \
    CHROME_DRIVER_VERSION=$(curl -sS chromedriver.storage.googleapis.com/LATEST_RELEASE_$(echo $CHROME_VERSION | cut -d. -f1)) && \
    wget -O /tmp/chromedriver.zip "https://chromedriver.storage.googleapis.com/${CHROME_DRIVER_VERSION}/chromedriver_linux64.zip" && \
    unzip /tmp/chromedriver.zip -d /usr/local/bin/ && \
    rm /tmp/chromedriver.zip

# Install BrowserMob Proxy
RUN wget -O /tmp/browsermob-proxy.zip \
    https://github.com/lightbody/browsermob-proxy/releases/download/browsermob-proxy-2.1.4/browsermob-proxy-2.1.4-bin.zip && \
    unzip /tmp/browsermob-proxy.zip -d /opt/ && \
    rm /tmp/browsermob-proxy.zip

ENV BROWSERMOB_PROXY_DIR=/opt/browsermob-proxy-2.1.4
ENV PATH="$BROWSERMOB_PROXY_DIR/bin:$PATH"

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy your application code
COPY . /app
WORKDIR /app

# Set the display port to avoid errors
ENV DISPLAY=:99

# Command to run your script
CMD ["python", "your_script.py"]
