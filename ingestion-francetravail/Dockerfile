FROM python:alpine3.19

WORKDIR /app
COPY requirements.txt ingestion-elasticsearch.py secrets.json ./
RUN pip install --no-cache-dir -r requirements.txt

# executer le shell
#CMD ["sh"]

# executer le script python au démarrage du conteneur
CMD [ "python", "./ingestion-elasticsearch.py"]