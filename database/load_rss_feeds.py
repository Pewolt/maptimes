import sys
import psycopg2
from psycopg2 import sql
import feedparser
from urllib.parse import urlparse
import datetime
import ssl
import configparser
from config import DB_CONFIG

def main(rss_url):
    # Verbindung zur Datenbank herstellen
    try:
        conn = psycopg2.connect(**DB_CONFIG)
    except Exception as e:
        print(f"Fehler bei der Verbindung zur Datenbank: {e}")
        sys.exit(1)

    cursor = conn.cursor()

    # Prüfen, ob der Feed bereits in der Datenbank existiert
    cursor.execute("SELECT id FROM rss_feeds WHERE url = %s;", (rss_url,))
    result = cursor.fetchone()

    if result:
        print("Der RSS-Feed ist bereits in der Datenbank vorhanden.")
    else:
        # SSL-Kontext erstellen
        ssl_context = ssl._create_unverified_context()

        # Feed auslesen und Metadaten extrahieren
        feed = feedparser.parse(rss_url, ssl_context=ssl_context)

        if feed.bozo:
            print(f"Fehler beim Parsen des Feeds: {feed.bozo_exception}")
            sys.exit(1)

        # Metadaten extrahieren
        feed_title = feed.feed.get('title', '').strip()
        feed_language = feed.feed.get('language', '').strip()
        feed_description = feed.feed.get('description', '').strip()

        # Hostname aus der URL extrahieren, falls kein Titel vorhanden
        if not feed_title:
            parsed_url = urlparse(rss_url)
            feed_title = parsed_url.netloc

        # Aktuelles Datum und Uhrzeit
        now = datetime.datetime.now()

        # Eintrag in die Datenbank einfügen
        insert_query = """
        INSERT INTO rss_feeds (url, name, language, description, status, created_at, updated_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s);
        """

        cursor.execute(insert_query, (
            rss_url,
            feed_title,
            feed_language,
            feed_description,
            'aktiv',
            now,
            now
        ))

        conn.commit()
        print("Der RSS-Feed wurde erfolgreich in die Datenbank eingefügt.")

    # Verbindung schließen
    cursor.close()
    conn.close()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Verwendung: python add_rss_feed.py <rss_feed_url>")
        sys.exit(1)

    rss_feed_url = sys.argv[1]
    main(rss_feed_url)
