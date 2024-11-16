import psycopg2
import feedparser
import hashlib
import spacy
import requests
import logging
import datetime
import configparser
import sys
from logging.handlers import RotatingFileHandler
from config import DB_CONFIG

# Logging-Konfiguration
logger = logging.getLogger('NewsMapParser')
logger.setLevel(logging.DEBUG)

# Formatter definieren
formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

# Rotating FileHandler für die Logdatei
file_handler = RotatingFileHandler('parse_news.log', maxBytes=5*1024*1024, backupCount=5)
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# StreamHandler für die Konsole
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

def main():
    logger.info('Starte das News Parsing Skript')

    # Verbindung zur Datenbank herstellen
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        logger.info('Erfolgreich mit der Datenbank verbunden')
    except Exception as e:
        logger.error(f'Fehler bei der Verbindung zur Datenbank: {e}', exc_info=True)
        sys.exit(1)

    # Sprachmodell laden
    try:
        nlp = spacy.load('de_core_news_sm')  # Passen Sie die Sprache an
        logger.info('Sprachmodell erfolgreich geladen')
    except Exception as e:
        logger.error(f'Fehler beim Laden des Sprachmodells: {e}', exc_info=True)
        cursor.close()
        conn.close()
        sys.exit(1)

    # Aktive Feeds abrufen
    try:
        cursor.execute("SELECT id, url, language FROM rss_feeds WHERE status = 'aktiv';")
        feeds = cursor.fetchall()
        logger.info(f'{len(feeds)} aktive Feeds aus der Datenbank abgerufen')
    except Exception as e:
        logger.error(f'Fehler beim Abrufen der Feeds: {e}', exc_info=True)
        cursor.close()
        conn.close()
        sys.exit(1)

    for feed_id, feed_url, feed_language in feeds:
        logger.info(f"Verarbeite Feed: {feed_url}")
        try:
            feed = feedparser.parse(feed_url)
            if feed.bozo:
                logger.warning(f'Probleme beim Parsen des Feeds {feed_url}: {feed.bozo_exception}')
                continue
        except Exception as e:
            logger.error(f'Fehler beim Abrufen des Feeds {feed_url}: {e}', exc_info=True)
            continue

        for entry in feed.entries:
            try:
                # Eindeutigen Hash erstellen
                unique_id = hashlib.sha256(entry.link.encode()).hexdigest()

                # Prüfen, ob der Artikel bereits vorhanden ist
                try:
                    cursor.execute("SELECT id FROM news WHERE unique_id = %s;", (unique_id,))
                    result = cursor.fetchone()
                except Exception as e:
                    logger.error(f'SQL-Fehler bei Prüfung auf vorhandenen Artikel: {e}', exc_info=True)
                    logger.debug(f'Abfrage: SELECT id FROM news WHERE unique_id = %s; Parameter: {unique_id}')
                    continue  # Zum nächsten Artikel

                if result:
                    logger.info(f'Artikel bereits vorhanden: {entry.link}')
                    continue  # Artikel existiert bereits

                # Artikelinformationen extrahieren
                title = entry.title
                description = entry.description
                publication_date = entry.published if 'published' in entry else datetime.datetime.now()

                # Ortsnamen extrahieren
                doc = nlp(f"{title} {description}")
                locations = [ent.text for ent in doc.ents if ent.label_ in ('LOC', 'GPE')]

                if not locations:
                    logger.info(f'Keine Ortsangaben in Artikel gefunden: {entry.link}')
                    continue  # Keine Ortsangaben gefunden

                location_ids = []
                for loc in locations:
                    # Prüfen, ob der Ort bereits in der Datenbank ist
                    try:
                        cursor.execute("SELECT id FROM locations WHERE name = %s;", (loc,))
                        result = cursor.fetchone()
                    except Exception as e:
                        logger.error(f'SQL-Fehler bei Prüfung auf vorhandenen Ort: {e}', exc_info=True)
                        logger.debug(f'Abfrage: SELECT id FROM locations WHERE name = %s; Parameter: {loc}')
                        continue  # Zum nächsten Ort

                    if result:
                        location_id = result[0]
                        logger.info(f'Ort gefunden in DB: {loc} (ID: {location_id})')
                        location_ids.append(location_id)
                    else:
                        # Geokodierung durchführen
                        try:
                            response = requests.get(
                                'https://nominatim.openstreetmap.org/search',
                                params={'q': loc, 'format': 'json', 'limit': 1},
                                headers={'User-Agent': 'NewsMapParser/1.0'}
                            )
                            data = response.json()
                            if data:
                                lat = data[0]['lat']
                                lon = data[0]['lon']
                                # Ort in der Datenbank speichern
                                try:
                                    cursor.execute(
                                        "INSERT INTO locations (name, latitude, longitude) VALUES (%s, %s, %s) RETURNING id;",
                                        (loc, lat, lon)
                                    )
                                    location_id = cursor.fetchone()[0]
                                    conn.commit()
                                    logger.info(f'Neuer Ort hinzugefügt: {loc} (ID: {location_id})')
                                    location_ids.append(location_id)
                                except Exception as e:
                                    conn.rollback()
                                    logger.error(f'SQL-Fehler beim Einfügen eines neuen Ortes: {e}', exc_info=True)
                                    logger.debug(f'Abfrage: INSERT INTO locations (name, latitude, longitude) VALUES (%s, %s, %s); Parameter: {loc}, {lat}, {lon}')
                                    continue  # Zum nächsten Ort
                            else:
                                logger.warning(f'Keine Geokodierungsdaten für Ort gefunden: {loc}')
                        except Exception as e:
                            logger.error(f'Fehler bei der Geokodierung von {loc}: {e}', exc_info=True)
                            continue  # Zum nächsten Ort

                # Artikel in der Datenbank speichern
                try:
                    cursor.execute(
                        "INSERT INTO news (title, description, link, publication_date, feed_id, language, unique_id) VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id;",
                        (title, description, entry.link, publication_date, feed_id, feed_language, unique_id)
                    )
                    news_id = cursor.fetchone()[0]
                    conn.commit()
                    logger.info(f'Neuer Artikel gespeichert: {title} (ID: {news_id})')
                except Exception as e:
                    conn.rollback()
                    logger.error(f'SQL-Fehler beim Einfügen eines neuen Artikels: {e}', exc_info=True)
                    logger.debug(f'Abfrage: INSERT INTO news (...); Parameter: {title}, {description}, {entry.link}, {publication_date}, {feed_id}, {feed_language}, {unique_id}')
                    continue  # Zum nächsten Artikel

                # Beziehungen zu Orten speichern
                for location_id in location_ids:
                    try:
                        cursor.execute(
                            "INSERT INTO news_locations (news_id, location_id) VALUES (%s, %s);",
                            (news_id, location_id)
                        )
                    except Exception as e:
                        conn.rollback()
                        logger.error(f'SQL-Fehler beim Verknüpfen von Artikel und Ort: {e}', exc_info=True)
                        logger.debug(f'Abfrage: INSERT INTO news_locations (news_id, location_id) VALUES (%s, %s); Parameter: {news_id}, {location_id}')
                        continue  # Zum nächsten Ort
                conn.commit()
                logger.info(f'Artikel-ID {news_id} mit Orten verknüpft')

            except Exception as e:
                logger.error(f'Fehler bei der Verarbeitung eines Artikels aus {feed_url}: {e}', exc_info=True)
                continue  # Zum nächsten Artikel

    # Verbindung schließen
    cursor.close()
    conn.close()
    logger.info('Skript abgeschlossen')

if __name__ == "__main__":
    main()
