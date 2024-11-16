import psycopg2
import feedparser
from config import DB_CONFIG
import logging
from geopy.geocoders import Nominatim
import requests

# Logging konfigurieren
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

# Geolocator für Koordinatensuche
geolocator = Nominatim(user_agent="rss_feed_loader")

def validate_rss_link(url):
    """Prüft, ob ein RSS-Link gültig ist."""
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            logger.info(f"RSS-Link validiert: {url}")
            return True
        else:
            logger.error(f"Fehler beim Abrufen des RSS-Links: {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"Fehler bei der Validierung des RSS-Links '{url}': {e}")
        return False

def parse_feed(url):
    """Extrahiert Informationen aus einem RSS-Feed."""
    feed = feedparser.parse(url)
    if feed.bozo:
        logger.error(f"Fehler beim Parsen des RSS-Feeds: {feed.bozo_exception}")
        return None

    feed_data = {
        'url': url,
        'name': feed.feed.get('title', 'Unbekannt'),
        'description': feed.feed.get('description', None),
        'language': feed.feed.get('language', feed.feed.get('dc_language', None)),
        'publisher': feed.feed.get('dc_publisher', None),
    }
    logger.info(f"Feed-Daten extrahiert: {feed_data}")
    return feed_data

def get_location_data(country=None, city=None):
    """Ermittelt oder fragt den Benutzer nach Land und Stadt und generiert Koordinaten."""
    if not country:
        country = input("Bitte das Land eingeben: ").strip()
    if not city:
        city = input("Bitte die Stadt eingeben: ").strip()

    try:
        location = geolocator.geocode(f"{city}, {country}")
        if location:
            logger.info(f"Koordinaten gefunden: {location.latitude}, {location.longitude}")
            return country, city, location.latitude, location.longitude
        else:
            logger.warning(f"Keine Koordinaten für {city}, {country} gefunden.")
            return country, city, None, None
    except Exception as e:
        logger.error(f"Fehler bei der Generierung der Koordinaten: {e}")
        return country, city, None, None

def save_feed_to_db(feed_data):
    """Speichert den RSS-Feed in der Datenbank."""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()

        # Kategorie prüfen oder hinzufügen
        cursor.execute("""
            INSERT INTO categories (name)
            VALUES (%s)
            ON CONFLICT (name) DO NOTHING
            RETURNING id;
        """, (feed_data['category'],))
        category_id = cursor.fetchone()
        feed_data['category_id'] = category_id if category_id else None

        # RSS-Feed speichern
        cursor.execute("""
            INSERT INTO rss_feeds (url, name, language, country, city, latitude, longitude, category_id, description)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (url) DO NOTHING;
        """, (
            feed_data['url'],
            feed_data['name'],
            feed_data['language'],
            feed_data['country'],
            feed_data['city'],
            feed_data['latitude'],
            feed_data['longitude'],
            feed_data['category_id'],
            feed_data['description']
        ))
        conn.commit()
        logger.info(f"RSS-Feed '{feed_data['url']}' erfolgreich gespeichert.")
    except Exception as e:
        logger.error(f"Fehler beim Speichern des RSS-Feeds: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

def main():
    """Hauptprozess für das Laden der RSS-Feeds."""
    while True:
        rss_url = input("RSS-Link eingeben (oder 'stop' zum Beenden): ").strip()
        if rss_url.lower() == 'stop':
            logger.info("Programm beendet.")
            break

        # RSS-Link validieren
        if not validate_rss_link(rss_url):
            print("Ungültiger Link. Bitte versuchen Sie es erneut.")
            continue

        # Feed parsen
        feed_data = parse_feed(rss_url)
        if not feed_data:
            print("Fehler beim Parsen des Feeds. Bitte versuchen Sie es erneut.")
            continue

        # Kategorie hinzufügen
        feed_data['category'] = input("Kategorie des Feeds eingeben: ").strip()

        # Standortdaten ermitteln
        print("Versuche, Standortdaten zu ermitteln...")
        feed_data['country'], feed_data['city'], feed_data['latitude'], feed_data['longitude'] = get_location_data()

        # Feed speichern
        save_feed_to_db(feed_data)

if __name__ == "__main__":
    main()
