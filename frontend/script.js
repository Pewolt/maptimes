// Initialisierung der Karte
const map = L.map('map').setView([51.505, -0.09], 5);
const tileLayer = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 19 });
tileLayer.addTo(map);

let activeMarkers = new Set();
const markers = L.markerClusterGroup().addTo(map);

// API-Basis-URLs
const API_URL = 'http://peterwolters.org/api/news';
const CATEGORIES_URL = 'http://peterwolters.org/api/categories';

// Farben für Marker
const defaultColor = '#3388ff'; // Blau
const selectedColor = '#ff7800'; // Orange

// Funktion zum Laden der Feeds mit Nachrichten
async function loadFeedsAndNews(filters = {}) {
  const bounds = map.getBounds();
  filters.latitude_min = bounds.getSouthWest().lat;
  filters.latitude_max = bounds.getNorthEast().lat;
  filters.longitude_min = bounds.getSouthWest().lng;
  filters.longitude_max = bounds.getNorthEast().lng;

  filters = {
    ...getFilters(),
    feed_ids: Array.from(activeMarkers).join(','),
  };

  const params = new URLSearchParams({ ...filters });
  try {
    const response = await fetch(`${API_URL}?${params.toString()}`);
    if (!response.ok) {
      throw new Error(`Fehler beim Abrufen der Feeds und Nachrichten: ${response.status}`);
    }

    const data = await response.json();
    updateMap(data.feeds);
    updateNewsFeed(data.feeds);
  } catch (error) {
    console.error('Fehler beim Laden der Feeds und Nachrichten:', error);
  }
}

// Karte mit Feeds und Nachrichten aktualisieren
function updateMap(feeds) {
  markers.clearLayers();

  feeds.forEach(feed => {
    if (feed.news_count > 0) {
      const markerSize = getMarkerSize(feed.news_count);
      const color = activeMarkers.has(feed.feed_id) ? selectedColor : defaultColor;

      const customIcon = L.divIcon({
        html: `<div style="
          background-color: ${color};
          width: ${markerSize * 2}px;
          height: ${markerSize * 2}px;
          border-radius: 50%;
          border: 2px solid #fff;
          box-sizing: border-box;
        "></div>`,
        className: '',
        iconSize: [markerSize * 2, markerSize * 2],
        iconAnchor: [markerSize, markerSize],
      });

      const marker = L.marker([feed.latitude, feed.longitude], { icon: customIcon });

      // Feed-ID und Nachrichtenanzahl speichern
      marker.feedId = feed.feed_id;
      marker.news_count = feed.news_count;

      marker.on('click', () => {
        toggleFeedSelection(marker);
      });

      // Tooltip hinzufügen
      marker.bindTooltip(`${feed.name} (${feed.news_count} Nachrichten)`);

      markers.addLayer(marker);
    }
  });

  // Sicherstellen, dass die Marker-Schicht zur Karte hinzugefügt wird
  if (!map.hasLayer(markers)) {
    map.addLayer(markers);
  }
}

// Marker-Größe basierend auf Nachrichtenanzahl
function getMarkerSize(newsCount) {
  const minSize = 5;
  const maxSize = 15;
  const maxNewsCount = 50; // Anpassen je nach Ihren Daten
  const size = minSize + (Math.min(newsCount, maxNewsCount) / maxNewsCount) * (maxSize - minSize);
  return size;
}

// Feeds auswählen oder abwählen
function toggleFeedSelection(marker) {
  const feedId = marker.feedId;

  if (activeMarkers.has(feedId)) {
    activeMarkers.delete(feedId);
    updateMarkerIcon(marker, defaultColor);
  } else {
    activeMarkers.add(feedId);
    updateMarkerIcon(marker, selectedColor);
  }

  // Kombination von feed_ids und anderen Filtern
  const filters = {
    ...getFilters(),
    feed_ids: Array.from(activeMarkers).join(','),
  };

  loadFeedsAndNews(filters);
}

// Marker-Icon aktualisieren
function updateMarkerIcon(marker, color) {
  const markerSize = getMarkerSize(marker.news_count);
  const customIcon = L.divIcon({
    html: `<div style="
      background-color: ${color};
      width: ${markerSize * 2}px;
      height: ${markerSize * 2}px;
      border-radius: 50%;
      border: 2px solid #fff;
      box-sizing: border-box;
    "></div>`,
    className: '',
    iconSize: [markerSize * 2, markerSize * 2],
    iconAnchor: [markerSize, markerSize],
  });
  marker.setIcon(customIcon);
}

// Nachrichtenfeed aktualisieren
function updateNewsFeed(feeds) {
  const newsListContainer = document.getElementById('news-list');
  newsListContainer.innerHTML = '';

  if (!feeds || feeds.length === 0) {
    newsListContainer.innerHTML = '<p>Keine Nachrichten gefunden.</p>';
    return;
  }

  feeds.forEach(feed => {
    if (feed.news.length > 0) {
      const feedHeader = document.createElement('h5');
      feedHeader.textContent = `${feed.name} (${feed.news_count} Nachrichten)`;
      newsListContainer.appendChild(feedHeader);

      feed.news.forEach(newsItem => {
        const newsCard = document.createElement('div');
        newsCard.className = 'news-card bg-white border p-2 m-1 rounded shadow-sm';
        newsCard.innerHTML = `
          <strong>${newsItem.title}</strong><br>
          ${newsItem.description.substring(0, 50)}...<br>
          <button class="btn btn-link p-0" onclick='showNewsPopup(${JSON.stringify(newsItem)})'>Mehr</button>
        `;
        newsListContainer.appendChild(newsCard);
      });
    }
  });
}

// Nachrichten-Popup anzeigen
function showNewsPopup(newsItem) {
  const popup = document.getElementById('news-popup');

  // Titel und Beschreibung
  document.getElementById('popup-title').textContent = newsItem.title;
  document.getElementById('popup-description').textContent = newsItem.description;

  // Veröffentlichungsdatum
  const publicationDate = newsItem.publication_date
    ? new Date(newsItem.publication_date).toLocaleString()
    : 'Nicht verfügbar';
  document.getElementById('popup-publication-date').textContent = publicationDate;

  // Herausgeber (Feed-Name)
  const publisher = newsItem.feed?.name || 'Unbekannt';
  document.getElementById('popup-publisher').textContent = publisher;

  // Link
  document.getElementById('popup-link').href = newsItem.link;

  // Popup anzeigen
  popup.classList.remove('d-none');
}

// Setze Standardzeitraum auf eine Woche
function setDefaultDateRange() {
  const endDate = new Date();
  const startDate = new Date();
  startDate.setDate(endDate.getDate() - 7);

  // Formatierung in YYYY-MM-DD für die Eingabefelder
  const formatDate = (date) => date.toISOString().split('T')[0];
  
  document.getElementById('filter-start-date').value = formatDate(startDate);
  document.getElementById('filter-end-date').value = formatDate(endDate);
}


// Popup schließen
document.getElementById('close-popup').addEventListener('click', () => {
  document.getElementById('news-popup').classList.add('d-none');
});

// Filter anwenden
document.getElementById('apply-filters').addEventListener('click', () => {
  activeMarkers.clear(); // Ausgewählte Feeds zurücksetzen
  loadFeedsAndNews(getFilters());
});

// Auswahl aufheben
document.getElementById('clear-selection').addEventListener('click', () => {
  activeMarkers.clear();
  loadFeedsAndNews(getFilters());
});

document.addEventListener('DOMContentLoaded', () => {
  setDefaultDateRange();
  loadCategories();
  loadFeedsAndNews(getFilters());
});


// Filter-Daten sammeln
function getFilters() {
  return {
    search: document.getElementById('filter-keyword').value,
    category: document.getElementById('filter-category').value,
    start_date: document.getElementById('filter-start-date').value,
    end_date: document.getElementById('filter-end-date').value,
  };
}

// Kategorien laden
async function loadCategories() {
  try {
    const response = await fetch(CATEGORIES_URL);
    if (!response.ok) {
      throw new Error(`Fehler beim Abrufen der Kategorien: ${response.status}`);
    }
    const data = await response.json();

    const categorySelect = document.getElementById('filter-category');
    categorySelect.innerHTML = '<option value="">Alle Kategorien</option>'; // Standardoption

    data.categories.forEach(category => {
      const option = document.createElement('option');
      option.value = category;
      option.textContent = category.charAt(0).toUpperCase() + category.slice(1);
      categorySelect.appendChild(option);
    });
  } catch (error) {
    console.error('Fehler beim Laden der Kategorien:', error);
  }
}

// Kartenbewegung
map.on('moveend', () => {
  loadFeedsAndNews(getFilters());
});

// Initiale Ladeprozesse
loadCategories();
loadFeedsAndNews(getFilters());
