# Projektstand eGrep Notes 3.0

20.11.2026. Autor Michael Nowak & KI.
Paket de.michaelnowak.egrepnotes; versionCode 30; Datenformatversion 9 (unveraendert).
Signiert mit dem Original-Schluessel (Zertifikat EE:80:AC:0D...2D:77); der Schluessel liegt nicht im Repo.

Aufbau seit 3.0:
- build_apk.py erzeugt Manifest und resources.arsc (byte-gleich zu 2.9 geprueft), packt die Oberflaeche
  aus app/src/main/assets und signiert (JAR/v1, OpenSSL CMS).
- native/classes.dex ist der unveraenderte Android-Host aus 2.9 (WebView, Kamera/Galerie, Drucken,
  Projektlink, Bildschirm-an, Zurueck-Taste, App-Verknuepfung "Schiri-Zeichen"). Der Generator-Quelltext
  dafuer ist verloren; native/decompiled/ enthaelt eine dekompilierte Lesefassung (androguard), die nicht
  zum Bauen dient. Aenderungen am nativen Teil brauchen einen neuen Host (z. B. Java + Android SDK).
- assets/ocr-data.js (Tesseract-Worker, Core, deutsches Modell) liegt fertig gebuendelt bei.

Neu 3.0: assets/clubs.js (window.EGREP_CLUBS: id, name, full, region, logo; 43 EHV-Mitgliedsvereine,
WebP 96 px; Neusser EV -> nev-logo.png). localStorage 'egrep-settings' {homeClub:id} oder {homeCustom:Name}.
app.js: homeClub(), freshState() (Heimname neuer Spiele), applyClub() (Kopfzeile, Info), Dialog
#settings-dialog (Suche #club-search, Liste #club-list, eigener Name #club-custom, #settings-reset),
Menuepunkt #open-settings. teamLogo(): Heimname = gewaehlter Verein -> dessen Wappen. Farben unveraendert.
Neu 2.9: Strafe-Felder servedBy/servedLater, L.needsServer, Wizard-Stufen 'served'/'servedBy';
OCR-Zweitdurchgang fuer Pos./Nr.; PDF-Import mit pdf.js 3.11.174 (isEvalSupported:false);
App-Verknuepfung (index.html#signs, window.egrepOpenSigns).


Neu 2.8: Kopfzeile #open-menu oeffnet <dialog id="quick-menu"> mit #show-signs, #menu-archive, #show-info.
Neu 2.7: Ereignistypen 'penaltyshot' (player, scored:boolean; L.isGoal) und 'note' (text, team '' = Allgemein,
L.cleanNote, NOTE_MAX 300); L.emptyNetGoal(state,e) ueber goalieAt des Gegners. Wizard-Stufen 'psresult', 'note';
Team-Knopf data-team="none" nur bei Notiz. DATA_VERSION bleibt 9 (neue Felder optional).
Neu 2.6: .scoreboard als 5-spaltiges Raster (Team-divs display:contents), Namen -webkit-line-clamp 2;
.report-match mit .rm-logo/.rm-name; logoImg ohne Akzent (colors in teamlogos.js bleiben ungenutzt).
Neu 2.5: assets/teamlogos.js (window.EGREP_TEAM_LOGOS: logos[] WebP 96 px, colors[], names{}, bases{});
L.teamLogoIndex/normTeamName/baseTeamName; app teamLogo(side)/logoImg(). Signal-Uebersicht #signs-dialog
(Knopf #show-signs). signs.js: Cross-Check und Haken ersetzt (Quelle clean/11.png, clean/14.png).
Neu 2.4: state.meta.timeMode 'down'|'up'|'game' (ersetzt clockMode; Migration clockMode 'up' ->
'game'). upToClock/upLabel/upDigits fuer Hallenuhr aufwaerts; Anzeige ueber dispClock/dispClockLabel.
Reihenfolge-Pruefung unveraendert (vergleicht Spielzeit), daher bei steigender Uhr automatisch richtig.
Piktogramm-Karten: grid-template-columns minmax(0,1fr).
Neu 2.3: Piktogramm-Karten als Grid (Bild 108/92 px fest, Textzeile min. 2 Zeilen), grid-auto-rows max-content.
Neu 2.2: state.meta.clockMode 'down'|'up' (normalizeClockMode, Migration, Default 'down');
elapsedToClock(raw) -> {period,time,clock,elapsed}, elapsedDigits(event). Bei 'up' setzt der
Zeitschritt period/time/clock aus der Spielzeit; currentPeriod folgt neuen Eintraegen nach oben.
Undo behaelt clockMode. Bericht: #operator-report-summary + Stift; Info: #info-version aus L.VERSION.
Neu 2.1: PENALTIES nach Haeufigkeit sortiert (Stichprobe 27 EHV-Spiele, hockeydata-Spielberichte,
Okt. 2026; 241 Strafen mit Dauer > 0); Strafauswahl als eine scrollbare Liste (.penalty-list);
optionale Schiri-Zeichen (assets/signs.js, window.EGREP_SIGNS, 21 Eintraege / 20 Bilder,
176 px JPEG), Schalter per Geraet in localStorage 'egrep-notes-schirizeichen'.
Offen: Zuordnung der seltenen Codes GA-MI, MATCH, CRITIC, CH-PL zu App-Namen ungeklaert
(je 1-3 Vorkommen, daher ohne Einfluss auf die Sortierung oben).
EHV: keine Verlaengerung (vom Nutzer bestaetigt).
Neu 2.0: Strafmass 2+2/10 (+10 als zweiter Eintrag), leeres Tor ('EN'), Penaltyschiessen
(state.shootout, Sieger +1, n.P.), Archiv (localStorage 'egrep-notes-archiv-v1', max. 20),
Drittelergebnisse, PP/SH-Hinweis (runningPenalties: 2 Min. endet beim ersten Gegentor,
2+2/5 laufen voll, 10/Spieldauer ohne Einfluss; nur Hinweis).
Neu 1.9: Nummernraster (Stage 'pick') fuer Tor/Strafe, Tap-Reihenfolge T/A1/A2, Ziffernblock
als Ausweg ('Andere Nummer') und ohne Aufstellung.
Neu 1.8: OCR fuer echte eGrep-Boegen: Tabellenlinien entfernen (removeTableLines), Pos./Nr.-
Grenze aus Spaltenkoepfen, Namenszuordnung geometrisch, Namensende an "Lizenz", Klammer-
