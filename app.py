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

@app.route('/api/news', methods=['GET'])
def get_news_and_feeds_grouped():
    try:
        logger.info("Neue Anfrage an /api/news")
        logger.info(f"Query-Parameter: {request.args}")

        # Filter-Parameter
        filters = {
            'country': request.args.get('country'),
            'city': request.args.get('city'),
            'language': request.args.get('language'),
            'category': request.args.get('category'),
            'start_date': request.args.get('start_date'),
            'end_date': request.args.get('end_date'),
            'search': request.args.get('search'),
            'latitude_min': request.args.get('latitude_min'),
            'latitude_max': request.args.get('latitude_max'),
            'longitude_min': request.args.get('longitude_min'),
            'longitude_max': request.args.get('longitude_max'),
            'feed_ids': request.args.get('feed_ids')
        }

        feed_ids = filters.get('feed_ids', None)
        if feed_ids:
            feed_ids = [int(fid.strip()) for fid in feed_ids.split(',')]

        conn = get_db_connection()
        cursor = conn.cursor()

        # Erweiterte Suchfunktion
        search_clauses = []
        search_terms = []
        if filters['search']:
            words = filters['search'].split()
            for word in words:
                search_clauses.append("(n.title ILIKE %s OR n.description ILIKE %s)")
                search_terms.extend([f"%{word}%", f"%{word}%"])

        # Feeds mit Nachrichten
        query = sql.SQL("""
            SELECT rf.id AS feed_id, rf.name AS feed_name, c.name AS category, rf.country, rf.city,
                rf.latitude, rf.longitude,
                COUNT(n.id) AS news_count,
                COALESCE(json_agg(json_build_object(
                    'id', n.id,
                    'title', n.title,
                    'description', n.description,
                    'publication_date', n.publication_date,
                    'link', n.link
                )) FILTER (WHERE n.id IS NOT NULL), '[]') AS news
            FROM rss_feeds rf
            LEFT JOIN news n ON rf.id = n.feed_id
            LEFT JOIN categories c ON rf.category_id = c.id
            WHERE 1=1
        """)

        where_clauses = []
        params = []

        # Dynamische Filter hinzufügen
        if filters['country']:
            where_clauses.append(sql.SQL("rf.country ILIKE %s"))
            params.append(f"%{filters['country']}%")
        if filters['city']:
            where_clauses.append(sql.SQL("rf.city ILIKE %s"))
            params.append(f"%{filters['city']}%")
        if filters['category']:
            where_clauses.append(sql.SQL("c.name = %s"))
            params.append(filters['category'])
        if filters['latitude_min'] and filters['latitude_max']:
            where_clauses.append(sql.SQL("rf.latitude BETWEEN %s AND %s"))
            params.extend([filters['latitude_min'], filters['latitude_max']])
        if filters['longitude_min'] and filters['longitude_max']:
            where_clauses.append(sql.SQL("rf.longitude BETWEEN %s AND %s"))
            params.extend([filters['longitude_min'], filters['longitude_max']])
        if feed_ids:
            where_clauses.append(sql.SQL("rf.id IN ({})").format(
                sql.SQL(', ').join(sql.Placeholder() * len(feed_ids))
            ))
            params.extend(feed_ids)
        if filters['start_date']:
            where_clauses.append(sql.SQL("n.publication_date >= %s"))
            params.append(filters['start_date'])
        if filters['end_date']:
            where_clauses.append(sql.SQL("n.publication_date <= %s"))
            params.append(filters['end_date'])
        if search_clauses:
            where_clauses.append(sql.SQL(" AND ").join(sql.SQL(clause) for clause in search_clauses))
            params.extend(search_terms)

        if where_clauses:
            query += sql.SQL(" AND ") + sql.SQL(" AND ").join(where_clauses)

        query += sql.SQL("""
            GROUP BY rf.id, rf.name, c.name, rf.country, rf.city, rf.latitude, rf.longitude
            ORDER BY rf.name
        """)

        logger.info(f"Feeds mit Nachrichten SQL: {query.as_string(conn)}")
        logger.info(f"Parameter: {params}")
        cursor.execute(query, params)
        records = cursor.fetchall()

        # Ergebnisse formatieren
        feeds = [{
            'feed_id': row[0],
            'name': row[1],
            'category': row[2],
            'country': row[3],
            'city': row[4],
            'latitude': row[5],
            'longitude': row[6],
            'news_count': row[7],
            'news': row[8]
        } for row in records]

        return jsonify({'feeds': feeds}), 200

    except Exception as e:
        logger.error(f"Fehler bei der Verarbeitung der Anfrage: {e}")
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
