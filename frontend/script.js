// --------------------------------------
// Initialisierung der Karte
// --------------------------------------
const map = L.map('map').setView([51.505, -0.09], 5);
const tileLayer = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 19 });
tileLayer.addTo(map);

const markers = L.markerClusterGroup().addTo(map);
let activeMarkers = new Set();

// API-Basis-URLs
const API_URL = 'https://peterwolters.org/api/news';
const CATEGORIES_URL = 'https://peterwolters.org/api/categories';

// Farben für Marker
const defaultColor = '#3388ff';
const selectedColor = '#ff7800';

// --------------------------------------
// Utility-Funktionen
// --------------------------------------

// Elemente auswählen
const toggleFiltersButton = document.getElementById('toggle-filters');
const extendedFilters = document.getElementById('extended-filters');
const applyFiltersButton = document.getElementById('apply-filters');

// Toggle für erweiterte Filter
toggleFiltersButton.addEventListener('click', () => {
  extendedFilters.classList.toggle('d-none');
});

// Filter anwenden
applyFiltersButton.addEventListener('click', () => {
  extendedFilters.classList.add('d-none'); // Erweiterte Filter schließen
  const filters = getFilters();
  loadFeedsAndNews(filters); // Feeds und Nachrichten basierend auf Filtern laden
});

// Standard-Datum einstellen (z. B. letzte Woche)
function setDefaultDateRange() {
  const endDate = new Date();
  const startDate = new Date();
  startDate.setDate(endDate.getDate() - 7);

  const formatDate = (date) => date.toISOString().split('T')[0];
  document.getElementById('filter-start-date').value = formatDate(startDate);
  document.getElementById('filter-end-date').value = formatDate(endDate);
}

// Initialisierung
document.addEventListener('DOMContentLoaded', () => {
  setDefaultDateRange();
  loadCategories(); // Kategorien laden
  loadFeedsAndNews(getFilters()); // Initiale Feeds und Nachrichten laden
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

// Berechne Marker-Größe basierend auf Nachrichtenanzahl
function getMarkerSize(newsCount) {
  const minSize = 5;
  const maxSize = 15;
  const maxNewsCount = 50;
  return minSize + (Math.min(newsCount, maxNewsCount) / maxNewsCount) * (maxSize - minSize);
}

// --------------------------------------
// Daten laden
// --------------------------------------

// Kategorien laden
async function loadCategories() {
  try {
    const response = await fetch(CATEGORIES_URL);
    if (!response.ok) throw new Error(`Fehler beim Abrufen der Kategorien: ${response.status}`);
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

// Feeds und Nachrichten laden
async function loadFeedsAndNews(filters = {}) {
  const bounds = map.getBounds();
  filters.latitude_min = bounds.getSouthWest().lat;
  filters.latitude_max = bounds.getNorthEast().lat;
  filters.longitude_min = bounds.getSouthWest().lng;
  filters.longitude_max = bounds.getNorthEast().lng;

  const params = new URLSearchParams({ ...filters, feed_ids: Array.from(activeMarkers).join(',') });
  try {
    const response = await fetch(`${API_URL}?${params.toString()}`);
    if (!response.ok) throw new Error(`HTTP-Fehler! Status: ${response.status}`);
    const data = await response.json();

    updateMap(data.feeds);
    updateNewsFeed(data.feeds);
  } catch (error) {
    console.error('Fehler beim Laden der Feeds und Nachrichten:', error);
  }
}

// --------------------------------------
// Aktualisieren der UI
// --------------------------------------

// Karte aktualisieren
function updateMap(feeds) {
  markers.clearLayers();

  feeds.forEach(feed => {
    if (feed.news.length > 0) {
      const markerSize = getMarkerSize(feed.news.length);
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
      marker.feedId = feed.feed_id;
      marker.bindTooltip(`${feed.name} (${feed.news.length} Nachrichten)`);

      marker.on('click', () => toggleFeedSelection(marker));
      markers.addLayer(marker);
    }
  });

  if (!map.hasLayer(markers)) map.addLayer(markers);
}

function updateNewsFeed(feeds) {
  const newsListContainer = document.getElementById('news-list');
  newsListContainer.innerHTML = ''; // Vorherige Inhalte entfernen

  feeds.forEach(feed => {
    if (feed.news.length > 0) {
      feed.news.forEach(newsItem => {
        // Dynamische Karte
        const newsCard = document.createElement('div');
        newsCard.className = 'card news-card';
        newsCard.innerHTML = `
          <div class="card-body d-flex flex-column">
            <h5 class="card-title">${newsItem.title}</h5>
            <p class="card-text">${newsItem.description}</p>
            <div class="mt-auto">
              <p class="card-text mb-0"><small class="text-muted">${new Date(newsItem.publication_date).toLocaleString()}</small></p>
            </div>
          </div>
        `;
        // Klick-Event hinzufügen
        newsCard.addEventListener('click', () => {
          showNewsPopup(newsItem, feed.name);
        });

        newsListContainer.appendChild(newsCard);
      });
    }
  });
}

// --------------------------------------
// Marker-Interaktionen
// --------------------------------------

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

  loadFeedsAndNews(getFilters());
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

// --------------------------------------
// Nachrichten-Popup
// --------------------------------------
// Nachrichten-Popup anzeigen
function showNewsPopup(newsItem, feedName) {
  const popup = document.getElementById('news-popup');

  // Titel und Beschreibung
  document.getElementById('popup-title').textContent = newsItem.title;
  document.getElementById('popup-description').textContent = newsItem.description;

  // Veröffentlichungsdatum
  const publicationDate = newsItem.publication_date
    ? new Date(newsItem.publication_date).toLocaleString()
    : 'Nicht verfügbar';
  document.getElementById('popup-publication-date').textContent = publicationDate;

  // Herausgeber
  const publisher = feedName || 'Unbekannt';
  document.getElementById('popup-publisher').textContent = publisher;

  // Link
  document.getElementById('popup-link').href = newsItem.link;

  // Popup anzeigen
  popup.classList.remove('d-none');
}

// Popup schließen
document.getElementById('close-popup').addEventListener('click', () => {
  document.getElementById('news-popup').classList.add('d-none');
});

// --------------------------------------
// Ereignisse und Initialisierung
// --------------------------------------
document.addEventListener('DOMContentLoaded', () => {
  setDefaultDateRange();
  loadCategories();
  loadFeedsAndNews(getFilters());
});

map.on('moveend', () => {
  loadFeedsAndNews(getFilters());
});
