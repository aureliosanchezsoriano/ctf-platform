FROM python:3.11-slim

WORKDIR /app

RUN pip install flask --no-cache-dir

COPY app/ .

# Entrypoint initializes DB and starts the app
CMD ["python", "-c", "import app; app.init_db(); app.app.run(host='0.0.0.0', port=5000)"]
