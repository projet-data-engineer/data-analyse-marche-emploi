FROM python:alpine3.19

WORKDIR /usr/src/app
COPY requirements.txt ingestion-api-france-travail.py ./
RUN pip install --no-cache-dir -r requirements.txt

#CMD ["sh"]
CMD [ "python", "./ingestion-api-france-travail.py"]

# docker build -t ingestion .
# docker run -it --rm --name ingestion ingestion