from flask import Flask, request, jsonify
from flask_cors import CORS
import psycopg2
from psycopg2 import sql
from config import DB_CONFIG
import logging

# Flask-App initialisieren
app = Flask(__name__)
CORS(app)

# Logging konfigurieren
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

# Datenbankverbindung herstellen
def get_db_connection():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        logger.error(f"Fehler bei der Datenbankverbindung: {e}")
        raise

## Endpunkt: Nachrichten abrufen
@app.route('/api/news', methods=['GET'])
def get_news():
    try:
        # Logs zur Anfrage
        logger.info("Neue Anfrage an /news:")
        logger.info(f"Query-Parameter: {request.args}")

        # Pagination-Parameter
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 10)), 100)
        offset = (page - 1) * per_page

        # Filter-Parameter
        filters = {
            'country': request.args.get('country'),
            'city': request.args.get('city'),
            'language': request.args.get('language'),
            'category': request.args.get('category'),
            'start_date': request.args.get('start_date'),
            'end_date': request.args.get('end_date'),
            'search': request.args.get('search'),
            'feed_ids': request.args.getlist('feed_ids'),
            'latitude_min': request.args.get('latitude_min'),
            'latitude_max': request.args.get('latitude_max'),
            'longitude_min': request.args.get('longitude_min'),
            'longitude_max': request.args.get('longitude_max')
        }
        
        # feed_ids parsen
        if filters['feed_ids']:
            feed_ids = [int(fid.strip()) for fid in filters['feed_ids'][0].split(',')]
        else:
            feed_ids = []

        # Basis-SQL-Abfrage
        query = sql.SQL("""
            SELECT n.id, n.title, n.description, n.link, n.publication_date, n.feed_id,
                rf.name AS feed_name, rf.country, rf.city, rf.latitude, rf.longitude, c.name AS category
            FROM news n
            JOIN rss_feeds rf ON n.feed_id = rf.id
            LEFT JOIN categories c ON rf.category_id = c.id
            WHERE 1=1
        """)

        where_clauses = []
        params = []

        # Dynamische Filter hinzufügen
        if filters['country']:
            where_clauses.append(sql.SQL("rf.country ILIKE %s"))
            params.append(f"%{filters['country']}%")
            logger.info(f"Filter: country = {filters['country']}")
        if filters['city']:
            where_clauses.append(sql.SQL("rf.city ILIKE %s"))
            params.append(f"%{filters['city']}%")
            logger.info(f"Filter: city = {filters['city']}")
        if filters['language']:
            where_clauses.append(sql.SQL("rf.language = %s"))
            params.append(filters['language'])
            logger.info(f"Filter: language = {filters['language']}")
        if filters['category']:
            where_clauses.append(sql.SQL("c.name = %s"))
            params.append(filters['category'])
            logger.info(f"Filter: category = {filters['category']}")
        if filters['start_date']:
            where_clauses.append(sql.SQL("n.publication_date >= %s"))
            params.append(filters['start_date'])
            logger.info(f"Filter: start_date = {filters['start_date']}")
        if filters['end_date']:
            where_clauses.append(sql.SQL("n.publication_date <= %s"))
            params.append(filters['end_date'])
            logger.info(f"Filter: end_date = {filters['end_date']}")
        if filters['search']:
            where_clauses.append(sql.SQL("(n.title ILIKE %s OR n.description ILIKE %s)"))
            search_term = f"%{filters['search']}%"
            params.extend([search_term, search_term])
            logger.info(f"Filter: search = {filters['search']}")
        if filters['feed_ids']:
            placeholders = sql.SQL(', ').join(sql.Placeholder() * len(feed_ids))
            where_clauses.append(sql.SQL("n.feed_id IN ({})").format(placeholders))
            params.extend(feed_ids)


        # Filter basierend auf Kartenkoordinaten
        if filters['latitude_min'] and filters['latitude_max']:
            where_clauses.append(sql.SQL("rf.latitude BETWEEN %s AND %s"))
            params.extend([filters['latitude_min'], filters['latitude_max']])
            logger.info(f"Filter: latitude_min = {filters['latitude_min']}, latitude_max = {filters['latitude_max']}")
        if filters['longitude_min'] and filters['longitude_max']:
            where_clauses.append(sql.SQL("rf.longitude BETWEEN %s AND %s"))
            params.extend([filters['longitude_min'], filters['longitude_max']])
            logger.info(f"Filter: longitude_min = {filters['longitude_min']}, longitude_max = {filters['longitude_max']}")

        # WHERE-Klauseln korrekt anhängen
        if where_clauses:
            query += sql.SQL(" AND ") + sql.SQL(" AND ").join(where_clauses)

        # Sortierung und Pagination
        query += sql.SQL("""
            ORDER BY n.publication_date DESC
            LIMIT %s OFFSET %s
        """)
        params.extend([per_page, offset])

        # Abfrage für Logs lesbar machen
        conn = get_db_connection()
        query_str = query.as_string(conn)  # Konvertiert die Abfrage in reinen SQL-Text
        logger.info(f"SQL-Abfrage wird ausgeführt: {query_str}")
        logger.info(f"Parameter: {params}")

        # Abfrage ausführen
        cursor = conn.cursor()
        cursor.execute(query, params)
        records = cursor.fetchall()
        logger.info(f"{len(records)} Ergebnisse gefunden.")

        # Ergebnisse formatieren
        news_list = []
        for row in records:
            news_item = {
                'id': row[0],
                'title': row[1],
                'description': row[2],
                'link': row[3],
                'publication_date': row[4].isoformat() if row[4] else None,
                'feed': {
                    'id': row[5],
                    'name': row[6],
                    'country': row[7],
                    'city': row[8],
                    'latitude': row[9],
                    'longitude': row[10]
                },
                'category': row[11]
            }
            news_list.append(news_item)

        # Ergebnisse zurückgeben
        logger.info(f"Erfolgreiche Verarbeitung der Anfrage. Ergebnisse: {len(news_list)}")
        return jsonify({'news': news_list, 'page': page, 'per_page': per_page}), 200

    except Exception as e:
        logger.error(f"Fehler bei der Verarbeitung der Anfrage: {e}")
        return jsonify({'error': 'Interner Serverfehler'}), 500

    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

# Endpunkt: Feeds mit Nachrichtenanzahl abrufen
@app.route('/api/feeds_with_counts', methods=['GET'])
def get_feeds_with_counts():
    try:
        # Filter-Parameter abrufen
        filters = {
            'category': request.args.get('category'),
            'start_date': request.args.get('start_date'),
            'end_date': request.args.get('end_date'),
            'search': request.args.get('search'),
            'latitude_min': request.args.get('latitude_min'),
            'latitude_max': request.args.get('latitude_max'),
            'longitude_min': request.args.get('longitude_min'),
            'longitude_max': request.args.get('longitude_max')
        }

        # Basis-SQL-Abfrage
        query = sql.SQL("""
            SELECT rf.id, rf.name, rf.latitude, rf.longitude, COUNT(n.id) as news_count
            FROM rss_feeds rf
            JOIN news n ON rf.id = n.feed_id
            LEFT JOIN categories c ON rf.category_id = c.id
            WHERE 1=1
        """)

        where_clauses = []
        params = []

        # Dynamische Filter hinzufügen
        if filters['category']:
            where_clauses.append(sql.SQL("c.name = %s"))
            params.append(filters['category'])
        if filters['start_date']:
            where_clauses.append(sql.SQL("n.publication_date >= %s"))
            params.append(filters['start_date'])
        if filters['end_date']:
            where_clauses.append(sql.SQL("n.publication_date <= %s"))
            params.append(filters['end_date'])
        if filters['search']:
            where_clauses.append(sql.SQL("(n.title ILIKE %s OR n.description ILIKE %s)"))
            search_term = f"%{filters['search']}%"
            params.extend([search_term, search_term])
        if filters['latitude_min'] and filters['latitude_max']:
            where_clauses.append(sql.SQL("rf.latitude BETWEEN %s AND %s"))
            params.extend([filters['latitude_min'], filters['latitude_max']])
        if filters['longitude_min'] and filters['longitude_max']:
            where_clauses.append(sql.SQL("rf.longitude BETWEEN %s AND %s"))
            params.extend([filters['longitude_min'], filters['longitude_max']])

        # WHERE-Klauseln anhängen
        if where_clauses:
            query += sql.SQL(" AND ") + sql.SQL(" AND ").join(where_clauses)

        # Gruppierung nach Feeds
        query += sql.SQL(" GROUP BY rf.id, rf.name, rf.latitude, rf.longitude")

        # Abfrage ausführen
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        records = cursor.fetchall()

        # Ergebnisse formatieren
        feeds = []
        for row in records:
            feed = {
                'feed_id': row[0],
                'name': row[1],
                'latitude': row[2],
                'longitude': row[3],
                'news_count': row[4]
            }
            feeds.append(feed)

        return jsonify({'feeds': feeds}), 200

    except Exception as e:
        logger.error(f"Fehler beim Abrufen der Feeds mit Nachrichtenanzahl: {e}")
        return jsonify({'error': 'Interner Serverfehler'}), 500

    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

# Endpunkt: Kategorien abrufen
@app.route('/api/categories', methods=['GET'])
def get_categories():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM categories ORDER BY name;")
        categories = [row[0] for row in cursor.fetchall()]
        return jsonify({'categories': categories}), 200
    except Exception as e:
        logger.error(f"Fehler beim Abrufen der Kategorien: {e}")
        return jsonify({'error': 'Interner Serverfehler'}), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

# Endpunkt: Feeds abrufen
@app.route('/api/feeds', methods=['GET'])
def get_feeds():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, url, country, city, language FROM rss_feeds ORDER BY name;")
        feeds = [
            {
                'id': row[0],
                'name': row[1],
                'url': row[2],
                'country': row[3],
                'city': row[4],
                'language': row[5]
            }
            for row in cursor.fetchall()
        ]
        return jsonify({'feeds': feeds}), 200
    except Exception as e:
        logger.error(f"Fehler beim Abrufen der Feeds: {e}")
        return jsonify({'error': 'Interner Serverfehler'}), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)
