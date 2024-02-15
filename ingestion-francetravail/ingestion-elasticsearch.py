import requests
import json
import time
import os
from datetime import datetime, timedelta
from threading import Thread

MAX_OFFRES = 3149

def authenticate(client_id, client_secret):

    url = 'https://entreprise.pole-emploi.fr/connexion/oauth2/access_token?realm=/partenaire'
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}    

    params = {
        'grant_type': 'client_credentials',
        'scope': 'api_offresdemploiv2 o2dsoffre'
    }

    params['client_id'] = client_id
    params['client_secret'] = client_secret

    response = requests.post(url=url,data=params,headers=headers)
    response = json.loads(response.text)
    return response['access_token']

def get_referentiel(url, access_token):

    headers = {'Authorization': f'Bearer {access_token}'}

    response = requests.get(url=url, headers=headers)
    response.raise_for_status
    response.encoding = 'utf-8'
    return response.text

def index_offres_elasticsearch(response):

    if response.status_code in (200, 206):

        resultats = json.loads(response.text)['resultats']

        if resultats is not None:

            ndjson = []

            for offre in resultats:

                ndjson.append(json.dumps({"index": {"_id": offre['id']}}))
                ndjson.append(json.dumps(offre))

            data = '\n'.join(d for d in ndjson)
            data += '\n'

            headers = {'Content-Type': 'application/x-ndjson'}
            requests.put(url=f'{os.getenv("ELASTICSEARCH_HOST")}/offres/_bulk', data=data, headers=headers)

def get_nb_total_offres(access_token):

    headers = {'Authorization': f'Bearer {access_token}'}

    response = requests.get(url=f"{os.getenv('FRANCETRAVAIL_HOST')}/partenaire/offresdemploi/v2/offres/search?range=0-5", headers=headers)
    content_range = response.headers['Content-Range']
    total = int(content_range.split(sep=' ')[1].split(sep='/')[1])
    return total

def search(url, access_token):

    headers = {'Authorization': f'Bearer {access_token}'}

    response = None

    try:

        start, end, total = (0, 0, 0)

        # execution requête
        response = requests.get(url=url,headers=headers)

        while response.status_code == 429: #429 Too Many Requests            
            
            retry_after = response.headers['Retry-After']
            time.sleep(int(retry_after))
            response = requests.get(url=url,headers=headers)     

        if 'Content-Range' in response.headers:

            content_range = response.headers['Content-Range']

            # NB: si aucun résultat content_range == "offres */0 communes"
            if int(content_range.split('/')[1]) == 0:
                start = 0
                end = 0
                total = 0            
            else:
                start = int(content_range.split(sep=' ')[1].split(sep='/')[0].split(sep='-')[0])
                end = int(content_range.split(sep=' ')[1].split(sep='/')[0].split(sep='-')[1])
                total = int(content_range.split(sep=' ')[1].split(sep='/')[1])

        else:
            
            start = 0
            end = 0
            total = 0

            erreur_data = {
                "query": url, 
                "message": "HTTP Header Content-Range absent", 
                "status_code": f"{response.status_code}", 
                "response": f"{response.text}"
            }

            requests.post(url='{os.getenv("ELASTICSEARCH_HOST")}/erreurs/_doc/', data=json.dumps(erreur_data), headers={'Content-Type': 'application/json'})

    except Exception as e:
        
        erreur_data = {
                "query": url, 
                "message": e, 
                "status_code": f"{response.status_code}", 
                "response": f"{response.text}"
        }

        requests.post(url='{os.getenv("ELASTICSEARCH_HOST")}/erreurs/_doc/', data=json.dumps(erreur_data), headers={'Content-Type': 'application/json'})

    finally:

        if response is not None:
            return start, end, total, response
        else:
            return start, end, total, None

def get_offres_region(region, departements, metiers, access_token):

    start = 0
    end = 149
    total = 0

    code = region["code"]
    libelle = region["libelle"]
   
    url = f"{os.getenv('FRANCETRAVAIL_HOST')}/partenaire/offresdemploi/v2/offres/search?range={start}-{end}&region={code}"
    start, end, total, response = search(url, access_token)

    print(f"Début itération région {code} {libelle} avec token {access_token}. Total offres disponibles: {total}")

    if total > MAX_OFFRES:

        departements_region = [ d for d in departements if d['region']['code'] == code ]

        for departement in departements_region:
            get_offres_departement(departement, metiers, access_token)

    else:

        if total > 0:

            index_offres_elasticsearch(response)

            while end < total - 1:

                start += 150
                end += 150

                url = f"{os.getenv('FRANCETRAVAIL_HOST')}/partenaire/offresdemploi/v2/offres/search?range={start}-{end}&region={code}"
                start, end, total, response = search(url, access_token)

                index_offres_elasticsearch(response)

def get_offres_departement(departement, metiers, access_token):

    start = 0
    end = 149
    total = 0

    url=f"{os.getenv('FRANCETRAVAIL_HOST')}/partenaire/offresdemploi/v2/offres/search?range={start}-{end}&departement={departement['code']}"
    start, end, total, response = search(url, access_token)

    if total > MAX_OFFRES:

        for metier in metiers:
            get_offres_departement_metier(departement, metier['code'], access_token)

    else:

        if total > 0:

            index_offres_elasticsearch(response)

            while end < total - 1:

                start += 150
                end += 150

                url=f"{os.getenv('FRANCETRAVAIL_HOST')}/partenaire/offresdemploi/v2/offres/search?range={start}-{end}&departement={departement['code']}"
                start, end, total, response = search(url, access_token)

                index_offres_elasticsearch(response)

def get_offres_departement_metier(departement, code_rome, access_token):

    start = 0
    end = 149
    total = 0
    
    url = f"{os.getenv('FRANCETRAVAIL_HOST')}/partenaire/offresdemploi/v2/offres/search?range={start}-{end}&departement={departement['code']}&codeROME={code_rome}"
    start, end, total, response = search(url, access_token)


    if total > MAX_OFFRES:

        print(f"{url.split('?')[1]}: total > MAX_OFFRES !")

    else:

        if total != 0:

            index_offres_elasticsearch(response)

            while end < total - 1:

                start += 150
                end += 150

                url = f"{os.getenv('FRANCETRAVAIL_HOST')}/partenaire/offresdemploi/v2/offres/search?range={start}-{end}&departement={departement['code']}&codeROME={code_rome}"
                start, end, total, response = search(url, access_token)

                index_offres_elasticsearch(response)

if __name__ == '__main__':

    # liste de couple key/secret renseignés dans le fichier secrets.json
    # Un couple key/secret = une application francetravail.io

    f = open("secrets.json")
    secrets = json.load(f)
    f.close()

    # liste de token d'authentification à attribuer aux Threads
    tokens = []

    for couple in secrets:
        tokens.append(authenticate(couple["key"], couple["secret"]))

    if len(tokens) > 0:    

        total_offres_api = get_nb_total_offres(access_token=tokens[0])

        debut_total = time.time()
        date_debut = datetime.now()

        print(f"\n\n{date_debut.strftime('%d/%m/%Y %H:%M:%S')}: démarrage collecte de {total_offres_api} offres d'emploi depuis API pole-emploi.io\n\n")

        # Création des index ElasticSearch    

        requests.delete(url=f'{os.getenv("ELASTICSEARCH_HOST")}/offres')
        requests.put(url=f'{os.getenv("ELASTICSEARCH_HOST")}/offres')
        
        requests.delete(url=f'{os.getenv("ELASTICSEARCH_HOST")}/erreurs')
        requests.put(url=f'{os.getenv("ELASTICSEARCH_HOST")}/erreurs')

        requests.delete(url=f'{os.getenv("ELASTICSEARCH_HOST")}/ingestion')
        requests.put(url=f'{os.getenv("ELASTICSEARCH_HOST")}/ingestion')

        # référentiels (pour itération des offres)

        url_referentiel = f"{os.getenv('FRANCETRAVAIL_HOST')}/partenaire/offresdemploi/v2/referentiel"

        regions = json.loads(get_referentiel(url=f'{url_referentiel}/regions', access_token=tokens[0])) #régions
        departements = json.loads(get_referentiel(url=f'{url_referentiel}/departements', access_token=tokens[0])) #départements
        metiers = json.loads(get_referentiel(url=f'{url_referentiel}/metiers', access_token=tokens[0])) #métiers (ROME)

        """
        Création des Threads d'ingestion pour chaque région
        Un token d'authentification est attribué à chaque Thread
        """

        threads = []
        indice_token = 0

        for region in regions:

            if indice_token > len(tokens) - 1:
                indice_token = 0

            threads.append(Thread(target=get_offres_region, args=(region, departements, metiers, tokens[indice_token])))
            indice_token += 1        

        [t.start() for t in threads]
        [t.join() for t in threads]   

        fin_total = time.time()

        hours = int((fin_total - debut_total) // 3600)
        minutes = int((fin_total - debut_total) // 60)

        duree_totale = ('0' + str(hours) if hours < 10 else str(hours)) + ':' + ('0' + str(minutes) if minutes < 10 else str(minutes))

        response_count = requests.get(url=f'{os.getenv("ELASTICSEARCH_HOST")}/offres/_count')
        response_count_json = json.loads(response_count.text)

        nb_offres = response_count_json['count']

        ingestion_data = {
            "message": "Fin ingestion des offres d'emploi depuis API pole-emploi.io",
            "date_debut": date_debut.strftime('%d/%m/%Y %H:%M:%S'),
            "date_fin": datetime.now().strftime('%d/%m/%Y %H:%M:%S'),
            "total_offres": total_offres_api,
            "total_offres_collecte": nb_offres,
            "duree_totale": duree_totale
        }

        headers = {'Content-Type': 'application/json'}
        requests.post(url=f'{os.getenv("ELASTICSEARCH_HOST")}/ingestion/_doc/', data=json.dumps(ingestion_data), headers=headers)

        print(f"\n\n{ingestion_data}\n\n")