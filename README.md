# Projet de Data analyse du marché de l'emploi

## Contexte et objectifs du projet

Il s'agit d'un projet de Data Engineering dans le cadre d'une formation à distance de Data Engineer (Datascientest.com).
Ce projet doit permettre de démontrer notre capacité à:

- Collecter et stocker des grandes quantités de données à partir de sources de données diverses et de les agréger
- Produire des analyses des données collectées, sous forme de tableaux de bord de visualisation de données
- Démontrer également notre capacité à appliquer et déployer des algorithme d'Intelligence Artificielle sur les données collectées. Une offre d'emploi comporte toujours un intitulé et une description, des données non structurées. L'application d'un algorithme de NLP sera étudié.

## Sources de données

- api francetravail.io
- ...

## francetravail.io (ex poleemploi.io)

Collecte des offres d'emploi depuis l'API Offres d'emploi de francetravail.io.

- Collecte des données réalisée avec succès.
- elasticsearch utilisé dans un premier temps par soucis de facilité (les données étant collectées au format json depuis l'API)
- Mais peut être pas le stockagele plus adéquat
- test en cours: stockage dans DuckDB

## Consigne d'execution locale

Créer un fichier **secrets.json** pour indiquer les **clés d'authentification à l'API**. Le fichier doit avoir la forme ci-dessus (un nombre variable de paires key/secret peuvent être renseignées)

```json
[
    {
        "key": "clé application déclarée sur francetravail.io",
        "secret": "secret application déclarée sur francetravail.io"
    },
    {
        "key": "clé application déclarée sur francetravail.io",
        "secret": "secret application déclarée sur francetravail.io"
    }
]
```

```bash
#!/bin/bash

cd ./ingestion-francetravail
docker-compose -f build
docker-compose -f up -d
```
