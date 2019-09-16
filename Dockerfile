FROM python:3.6
WORKDIR /app
COPY requirements.txt ./
ENV PYTHONPATH /src
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["python","./src/k8s_scheduler.py"]