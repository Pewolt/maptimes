-- Tabelle für Kategorien
CREATE TABLE categories (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabelle für RSS-Feeds
CREATE TABLE rss_feeds (
    id SERIAL PRIMARY KEY,
    url TEXT NOT NULL UNIQUE,
    name TEXT,
    language VARCHAR(10),
    country TEXT,
    city TEXT,
    latitude DECIMAL(9,6),
    longitude DECIMAL(9,6),
    category_id INTEGER REFERENCES categories(id) ON DELETE SET NULL,
    description TEXT,
    status VARCHAR(20) DEFAULT 'active',
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
    feed_id INTEGER REFERENCES rss_feeds(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabelle für Keywords
CREATE TABLE keywords (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Verknüpfungstabelle für Nachrichten und Keywords
CREATE TABLE news_keywords (
    news_id INTEGER REFERENCES news(id) ON DELETE CASCADE,
    keyword_id INTEGER REFERENCES keywords(id) ON DELETE CASCADE,
    PRIMARY KEY (news_id, keyword_id)
);
