# The base image ships Chromium for this exact Playwright version, but not the
# Python package, so install the matching one.
FROM mcr.microsoft.com/playwright/python:v1.49.0-jammy

RUN pip install --no-cache-dir playwright==1.49.0 pillow==11.0.0

WORKDIR /app
COPY server.py .
COPY pages pages

EXPOSE 8080
CMD ["python", "server.py"]
