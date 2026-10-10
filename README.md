# Analyse des tendances Wikimédia en temps réel

Projet Big Data (Projet 5, groupes 5 et 6) : pipeline complet d'analyse du flux des modifications Wikipédia en temps réel.

## Architecture

Flux Wikimedia (SSE) → Producer Python → Kafka → MongoDB + Spark Streaming → Dashboard Streamlit

## Technologies

- Python
- Apache Kafka
- MongoDB
- Apache Spark Streaming
- Streamlit

## Structure du projet

- `config/` : paramètres communs
- `producer/` : lecture du flux Wikimedia et envoi dans Kafka
- `consumer/` : stockage des événements dans MongoDB
- `spark/` : analyse de l'activité par minute et par sujet
- `dashboard/` : visualisation avec Streamlit
- `docs/` : schémas et captures d'écran

## Auteur

SOULI Wênd-Manegda Davy, ISSEA (ISE)
