FROM python:3.8-slim
COPY requirements.txt .
COPY *.py ./
RUN pip3 install -r requirements.txt
ENTRYPOINT ["python", "SERVICE_NAME.py"]