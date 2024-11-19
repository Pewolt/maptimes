# maptimes

**maptimes** ist eine Webanwendung, die Nachrichtenartikel aus allen Themenbereichen auf einer interaktiven Weltkarte visualisiert. Sie zeigt, wo auf der Welt welche Nachrichten veröffentlicht werden und wie häufig. Durch die geografische Darstellung von Nachrichtenquellen und deren Veröffentlichungen ermöglicht **maptimes** Nutzern, globale Ergebnisse zu ihren Lieblingsthemen und Ereignissen zu finden und verschiedene Sichtweisen aus der ganzen Welt zu entdecken.

Das Ziel von **maptimes** ist es, eine vielseitige und globalere Perspektive auf Themen und Nachrichten zu fördern. Es richtet sich an alle, die interessiert sind, die Vielfalt der weltweiten Berichterstattung zu erleben und ein umfassenderes Verständnis für globale Ereignisse zu entwickeln.

## Überblick

- **Interaktive Kartenvisualisierung**: Nachrichten-Feeds werden als kreisförmige Marker auf der Karte angezeigt. Die Größe jedes Kreises repräsentiert die Anzahl der verfügbaren Nachrichtenartikel von diesem Feed.

- **Feed-Auswahl**: Nutzer können durch Klicken auf die Marker mehrere Feeds auswählen. Ausgewählte Feeds werden hervorgehoben, und ihre zugehörigen Nachrichtenartikel werden im Nachrichtenfeed angezeigt.

- **Nachrichtenfeed-Anzeige**: Die Anwendung präsentiert eine scrollbare Liste von Nachrichtenartikeln aus den ausgewählten Feeds, wobei Nutzer Zusammenfassungen lesen und auf vollständige Artikel zugreifen können.

- **Filteroptionen**: Nutzer können Nachrichten nach Kategorien, Stichwörtern und Zeiträumen filtern, um die angezeigten Inhalte an ihre Interessen anzupassen.

- **Clustering**: Bei herausgezoomter Ansicht werden nahe beieinander liegende Feeds zu Clustern zusammengefasst, um eine übersichtliche Kartendarstellung zu gewährleisten.

## Features

- **Geografische Nachrichtenerkundung**: Entdecken Sie Nachrichten aus aller Welt, indem Sie die Karte navigieren und interessante Regionen auswählen.

- **Dynamische Visualisierung**: Die Markierungsgröße passt sich dynamisch basierend auf der Anzahl der Nachrichtenartikel an und bietet sofortige visuelle Hinweise auf die Aktivität der Feeds.

- **Mehrfachauswahl von Feeds**: Erweitern Sie Ihren Nachrichtenkonsum, indem Sie mehrere Feeds gleichzeitig auswählen und aggregierte Inhalte anzeigen.

- **Benutzerfreundliche Oberfläche**: Ein intuitives Design, das Karteninteraktion mit traditionellem Nachrichtenlesen kombiniert, für ein verbessertes Benutzererlebnis.

## Verwendete Technologien

## Projektstruktur

## Installation

## TODO

- **Suche verbessern**: Statt nach genauem Text zu suchen, verwerte die einzelnen Worte bei der Suche.

- **Übersetzen**: Titel und Text sollen ins Englisch ggf. auch Deutsch übersetzt werden.

- **Frontend**
    - **Reload** der API Abfrage jede Minute
    - **Responsive** design, fürs Handy optimieren
    - **News-Feed-Cards** sollen immer die selbe größe haben
    - **favicon** hinzufügen
    - **Titel** umbenennen
    - **Suche** nach links, weitere Filter hinzufügen, verschönern und nicht wichtige Filter einklappen
    - **Karteneinstellungen** hinzufügen, Zoomen nach rechts verschieben, Karten-Design-Auswahl anbieten
    - **Standartzoom** auf gesammte Welt und mittig
    - **Unendliche Karte** deaktivieren
    - **Linie** zwischen News-Karte und Kartenmarkierung ziehen
    - **Ausgeklappte Karte** soll mehr Infos anzeigen, wie Herausgeber und Datum

- **API**: Falls möglich, könnten Sie die Backend-API so erweitern, dass die Feeds bereits mit den gefilterten Nachrichtenanzahlen zurückgegeben werden. Dies würde die Notwendigkeit, die Nachrichtenanzahlen im Frontend zu zählen, eliminieren und die Effizienz verbessern.