// 1. Initialisierung der Karte
const map = L.map('map').setView([51.505, -0.09], 5);
const tileLayer = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
  maxZoom: 19
});
tileLayer.addTo(map);

let activeMarker = null;

// API-Basis-URL
const API_URL = 'http://127.0.0.1:5000/news';

// Nachrichten laden und auf der Karte anzeigen
async function loadNews(filters = {}) {
  const params = new URLSearchParams({
    page: 1,
    per_page: 100,
    ...filters
  });

  const response = await fetch(`${API_URL}?${params.toString()}`);
  const data = await response.json();

  updateMap(data.news);
}

// Karte mit Nachrichten aktualisieren
function updateMap(newsList) {
  map.eachLayer(layer => {
    if (layer !== tileLayer) {
      map.removeLayer(layer);
    }
  });

  newsList.forEach(newsItem => {
    newsItem.locations.forEach(location => {
      const circle = L.circleMarker([location.latitude, location.longitude], {
        radius: 8,
        color: 'blue',
        fillColor: '#3388ff',
        fillOpacity: 0.5
      });

      circle.on('click', () => {
        if (activeMarker) activeMarker.setStyle({ color: 'blue' });
        circle.setStyle({ color: 'red' });
        activeMarker = circle;
        showNewsDetails(newsItem);
      });

      circle.addTo(map);
    });
  });
}

// Nachrichten-Details anzeigen
function showNewsDetails(newsItem) {
  const details = document.getElementById('news-details');
  document.getElementById('news-title').textContent = newsItem.title;
  document.getElementById('news-description').textContent = newsItem.description;
  document.getElementById('news-link').href = newsItem.link;
  details.classList.remove('d-none');
}

// 2. Filter-Menü-Interaktionen
// Ein- und Ausklappen der Filterleiste
const toggleFilterButton = document.getElementById('toggle-filter');
const filterBar = document.getElementById('filter-bar');

toggleFilterButton.addEventListener('click', () => {
  filterBar.classList.toggle('d-none'); // Zeige/Verstecke die Filterleiste
});

// Event-Listener für den "Bestätigen"-Button
document.getElementById('apply-filters').addEventListener('click', () => {
  // Sammle die Filterdaten
  const category = document.getElementById('filter-category').value;
  const startDate = document.getElementById('filter-start-date').value;
  const endDate = document.getElementById('filter-end-date').value;
  const keyword = document.getElementById('filter-keyword').value;
  const language = document.getElementById('filter-language').value;

  // API-Abfrage mit den gesammelten Filtern
  const filters = {};
  if (category) filters.category = category;
  if (startDate) filters.start_date = startDate;
  if (endDate) filters.end_date = endDate;
  if (keyword) filters.search = keyword;
  if (language) filters.language = language;

  console.log('Filter angewendet:', filters);
  loadNews(filters);
});

// Event-Listener für den "Zurücksetzen"-Button
document.getElementById('reset-filters').addEventListener('click', () => {
  document.getElementById('filter-category').value = '';
  document.getElementById('filter-start-date').value = '';
  document.getElementById('filter-end-date').value = '';
  document.getElementById('filter-keyword').value = '';
  document.getElementById('filter-language').value = '';

  console.log('Filter zurückgesetzt');
  loadNews();
});

// 3. Kartensteuerung: Zoom-In und Zoom-Out
document.getElementById('zoom-in').addEventListener('click', () => {
  map.zoomIn();
});

document.getElementById('zoom-out').addEventListener('click', () => {
  map.zoomOut();
});

// Kartenstil wechseln
document.getElementById('toggle-style').addEventListener('click', () => {
  if (map.hasLayer(tileLayer)) {
    map.removeLayer(tileLayer);
    const satelliteLayer = L.tileLayer('https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png', {
      maxZoom: 17
    });
    satelliteLayer.addTo(map);
  } else {
    tileLayer.addTo(map);
  }
});

// 4. Initiale API-Abfrage
loadNews();
