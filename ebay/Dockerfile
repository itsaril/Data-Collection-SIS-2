FROM apache/airflow:2.9.1-python3.12

USER root

RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    curl \
    unzip \
    && rm -rf /var/lib/apt/lists/*


USER airflow

RUN pip install --no-cache-dir \
    selenium \
    webdriver-manager \
    beautifulsoup4 \
    pandas \
    lxml \
    requests
