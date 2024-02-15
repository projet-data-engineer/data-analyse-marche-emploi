FROM python:alpine3.19

WORKDIR /app
COPY requirements.txt ingestion-elasticsearch.py secrets.json ./
RUN pip install --no-cache-dir -r requirements.txt

# Executer le script python au démarrage du conteneur
# NB: supprime les indexs offres et ingestion

CMD [ "python", "./ingestion-elasticsearch.py"]