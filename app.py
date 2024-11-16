# app.py
from flask import Flask, jsonify, request
import psycopg2
from psycopg2 import sql
from config import DB_CONFIG
from flask_cors import CORS
import datetime

app = Flask(__name__)
CORS(app)

def get_db_connection():
    conn = psycopg2.connect(**DB_CONFIG)
    return conn

@app.route('/news', methods=['GET'])
def get_news():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Parameter für Pagination und Filter
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        offset = (page - 1) * per_page
        
        # Filterparameter
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        category = request.args.get('category')
        location = request.args.get('location')
        search = request.args.get('search')  # Stichwortsuche
        
        # Basis-SQL-Abfrage
        base_query = sql.SQL("""
            SELECT n.id, n.title, n.description, n.link, n.publication_date, n.feed_id,
                array_agg(DISTINCT jsonb_build_object(
                   'id', l.id,
                   'name', l.name,
                   'latitude', l.latitude,
                   'longitude', l.longitude
                )) AS locations,
                rf.category AS feed_category
            FROM news n
            JOIN news_locations nl ON n.id = nl.news_id
            JOIN locations l ON nl.location_id = l.id
            JOIN rss_feeds rf ON n.feed_id = rf.id
        """)
        
        where_clauses = []
        params = []
        
        # Filterbedingungen hinzufügen
        if start_date:
            where_clauses.append(sql.SQL("n.publication_date >= %s"))
            params.append(start_date)
        if end_date:
            where_clauses.append(sql.SQL("n.publication_date <= %s"))
            params.append(end_date)
        if category:
            where_clauses.append(sql.SQL("rf.category = %s"))
            params.append(category)
        if location:
            where_clauses.append(sql.SQL("l.name ILIKE %s"))
            params.append(f"%{location}%")
        if search:
            where_clauses.append(sql.SQL("(n.title ILIKE %s OR n.description ILIKE %s)"))
            params.extend([f"%{search}%", f"%{search}%"])
        
        # WHERE-Klausel konstruieren
        if where_clauses:
            where_clause = sql.SQL(" WHERE ") + sql.SQL(" AND ").join(where_clauses)
        else:
            where_clause = sql.SQL("")
        
        # GROUP BY, ORDER BY und LIMIT/OFFSET
        group_order_limit = sql.SQL("""
            GROUP BY n.id, n.title, n.description, n.link, n.publication_date, n.feed_id, rf.category
            ORDER BY n.publication_date DESC
            LIMIT %s OFFSET %s
        """)
        params.extend([per_page, offset])
        
        # Endgültige Abfrage zusammenstellen
        query = base_query + where_clause + group_order_limit
        
        cursor.execute(query, params)
        records = cursor.fetchall()
        
        # Ergebnisse formatieren
        news_list = []
        for row in records:
            news_item = {
                'id': row[0],
                'title': row[1],
                'description': row[2],
                'link': row[3],
                'publication_date': row[4].isoformat() if row[4] else None,
                'feed_id': row[5],
                'locations': row[6],
                'category': row[7]
            }
            news_list.append(news_item)
        
        return jsonify({'news': news_list}), 200
    
    except Exception as e:
        print(f'Fehler: {e}')
        return jsonify({'error': 'Interner Serverfehler'}), 500
    
    finally:
        cursor.close()
        conn.close()

# Zusätzlicher Endpunkt für Kategorien
@app.route('/categories', methods=['GET'])
def get_categories():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT category FROM rss_feeds WHERE category IS NOT NULL;")
        categories = [row[0] for row in cursor.fetchall()]
        return jsonify({'categories': categories}), 200
    except Exception as e:
        print(f'Fehler: {e}')
        return jsonify({'error': 'Interner Serverfehler'}), 500
    finally:
        cursor.close()
        conn.close()

# Zusätzlicher Endpunkt für Orte
@app.route('/locations', methods=['GET'])
def get_locations():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT name FROM locations;")
        locations = [row[0] for row in cursor.fetchall()]
        return jsonify({'locations': locations}), 200
    except Exception as e:
        print(f'Fehler: {e}')
        return jsonify({'error': 'Interner Serverfehler'}), 500
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    app.run(debug=True)
