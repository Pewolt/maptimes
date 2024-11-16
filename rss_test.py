import feedparser

# RSS-Feed-URL der Tagesschau
rss_url = "https://www.tagesschau.de/infoservices/alle-meldungen-100~rss2.xml"

# RSS-Feed laden
feed = feedparser.parse(rss_url)

# Feed-Informationen anzeigen
print(f"Feed-Titel: {feed['feed']['title']}")
print(f"Beschreibung: {feed['feed']['subtitle']}\n")

# Artikel ausgeben
print("Nachrichten:")
for entry in feed['entries'][:5]:  # Die ersten 5 Einträge anzeigen
    print(f"\nTitel: {entry['title']}")
    print(f"Link: {entry['link']}")
    print(f"Veröffentlicht: {entry.get('published', 'Keine Angabe')}")
    print(f"Zusammenfassung: {entry.get('summary', 'Keine Angabe')}")
