import psycopg2
from config import DB_CONFIG
import feedparser
import logging
from datetime import datetime

# Logging konfigurieren
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

def get_active_feeds():
    """Lädt alle aktiven RSS-Feeds aus der Datenbank."""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("SELECT id, url FROM rss_feeds WHERE status = 'active';")
        feeds = cursor.fetchall()
        conn.close()
        logger.info(f"{len(feeds)} aktive Feeds geladen.")
        return feeds
    except Exception as e:
        logger.error(f"Fehler beim Laden der aktiven Feeds: {e}")
        return []

def fetch_and_parse_feed(feed_url):
    """Lädt und parst einen RSS-Feed."""
    try:
        feed = feedparser.parse(feed_url)
        if feed.bozo:
            logger.warning(f"Fehler beim Parsen des Feeds: {feed.bozo_exception}")
            return None
        return feed.entries
    except Exception as e:
        logger.error(f"Fehler beim Abrufen und Parsen des Feeds '{feed_url}': {e}")
        return None

def save_news_to_db(feed_id, news_items):
    """Speichert Nachrichten in der Datenbank."""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        new_count = 0

        for item in news_items:
            # Nachrichtendaten vorbereiten
            title = item.get('title', 'Kein Titel')
            description = item.get('description', None)
            link = item.get('link', None)
            pub_date = item.get('published', None)

            # Veröffentlichungsdatum parsen
            publication_date = None
            if pub_date:
                try:
                    publication_date = datetime(*item.published_parsed[:6])
                except Exception as e:
                    logger.warning(f"Fehler beim Parsen des Veröffentlichungsdatums: {e}")

            # Nachricht speichern, wenn sie neu ist
            try:
                cursor.execute("""
                    INSERT INTO news (title, description, link, publication_date, feed_id)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (link) DO NOTHING;
                """, (title, description, link, publication_date, feed_id))
                if cursor.rowcount > 0:
                    new_count += 1
                    logger.info(f"Neue Nachricht gespeichert: {title}")
            except Exception as e:
                logger.error(f"Fehler beim Speichern der Nachricht '{title}': {e}")

        # Transaktion bestätigen
        conn.commit()
        logger.info(f"{new_count} neue Nachrichten für Feed ID {feed_id} gespeichert.")

    except Exception as e:
        logger.error(f"Fehler beim Speichern der Nachrichten: {e}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def main():
    """Hauptprozess für das Parsen und Speichern von Nachrichten."""
    feeds = get_active_feeds()

    for feed_id, feed_url in feeds:
        logger.info(f"Verarbeite Feed: {feed_url}")

        # Feed-Daten abrufen und parsen
        news_items = fetch_and_parse_feed(feed_url)
        if not news_items:
            logger.warning(f"Keine Daten für Feed {feed_url} gefunden.")
            continue

        # Nachrichten speichern
        save_news_to_db(feed_id, news_items)

if __name__ == "__main__":
    main()
