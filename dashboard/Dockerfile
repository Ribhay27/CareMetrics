FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends build-essential libgomp1 && rm -rf /var/lib/apt/lists/*
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt
COPY dashboard/ /app/dashboard/
COPY common/ /app/common/
COPY data/ /app/data/
ENV PROJECT_ROOT=/app
CMD ["streamlit", "run", "dashboard/app.py", "--server.address", "0.0.0.0", "--server.port", "8501"]
