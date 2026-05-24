FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /srv

COPY app/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY data/metadata ./data/metadata

EXPOSE 8001

CMD ["uvicorn", "app.naijarec_cold_start:app", "--host", "0.0.0.0", "--port", "8001"]
