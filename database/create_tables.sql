CREATE TABLE rss_feeds (
    id SERIAL PRIMARY KEY,
    url TEXT NOT NULL,
    name TEXT,
    language VARCHAR(10),
    country TEXT,
    city TEXT,
    latitude DECIMAL(9,6),
    longitude DECIMAL(9,6),
    category TEXT,
    description TEXT,
    status VARCHAR(20) DEFAULT 'aktiv',
    last_fetched TIMESTAMP,
    error_count INTEGER DEFAULT 0,
    fetch_interval INTEGER DEFAULT 60, -- in Minuten
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabelle für Nachrichten
CREATE TABLE news (
    id SERIAL PRIMARY KEY,
    title TEXT,
    description TEXT,
    link TEXT UNIQUE,
    publication_date TIMESTAMP,
    feed_id INTEGER REFERENCES rss_feeds(id),
    language VARCHAR(10),
    unique_id VARCHAR(64) UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabelle für Orte
CREATE TABLE locations (
    id SERIAL PRIMARY KEY,
    name TEXT UNIQUE,
    latitude DECIMAL(9,6),
    longitude DECIMAL(9,6),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Verknüpfungstabelle zwischen Nachrichten und Orten
CREATE TABLE news_locations (
    news_id INTEGER REFERENCES news(id),
    location_id INTEGER REFERENCES locations(id),
    PRIMARY KEY (news_id, location_id)
);
