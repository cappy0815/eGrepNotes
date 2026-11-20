# Projektstand eGrep Notes 3.1

18.10.2026. Autor Michael Nowak & KI.
Paket de.michaelnowak.egrepnotes; versionCode 31; Datenformatversion 9.
Aufbauend auf 2.7. Offline-Build mit Python/OpenSSL; Java/Gradle-Referenz enthalten.
Signiert mit dem Original-Schluessel aus der PRIVAT-Sicherung 1.4 (Zertifikat EE:80:AC:0D...2D:77).

Neu 3.1: Wischen zwischen den Reitern (touchstart/touchend auf <main>, Schwelle max(60 px, 18 % Breite), dx >= 2*dy,
< 700 ms; nicht in Eingabefeldern, seitlich scrollenden Bereichen oder bei offenem Dialog), Schalter #swipe-toggle,
settings.swipe (Standard an).
Neu 3.0: assets/clubs.js (window.EGREP_CLUBS: id, name, full, region, logo; 43 EHV-Vereine, Neusser EV -> nev-logo.png).
localStorage 'egrep-settings' {homeClub:id | homeCustom:Name, swipe}. homeClub(), freshState(), applyClub(),
#settings-dialog, Menuepunkt #open-settings. Farben unveraendert.
Neu 2.9: Strafe-Felder servedBy (Nummer) und servedLater (bool), L.needsServer(state,e) (Bank, TW in
Aufstellung oder L.goalieAt), L.servedLabel; participants enthaelt 'Sitzt ab'. Wizard-Stufen 'served' (Raster,
data-served-number) und 'servedBy' (Ziffernblock); finishPenalty() vor saveDraft. DATA_VERSION bleibt 9.
OCR: withNrHeaders, numberStrips/stripWords/missingNumberCells (zweiter Durchgang nur Ziffern), Split am
Gast-"Pos."-Kopf, sideEnd je Seite, alt -> check. PDF: assets/pdf.min.js + pdf.worker.min.js (pdf.js
3.11.174 legacy, Apache-2.0, ohne Worker, isEvalSupported:false), EgrepOCR.readPdf/pdfTextToTsv/startImage.
Nativ: dynamische Verknuepfung 'signs' (ShortcutManager in onCreate, try/catch), index.html#signs,
onNewIntent -> window.egrepOpenSigns().
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
nummern/Zusaetze aus Namen entfernt, G in Pos.-Spalte ab 35 %.
Grenze der Aussage: abgestimmt und gemessen an ZWEI echten Fotos (per Chat uebertragen, ggf.
komprimiert). Andere Lichtverhaeltnisse, Winkel oder Druckerqualitaet koennen abweichen.
Neu 1.7: TSV-Fix (Bildgroesse), Komma im Namen erlaubt.
Neu 1.6: Zusammenfassung nach Eingabe (gespeichert, OK/Aendern/Verwerfen), Detailansicht
per Antippen, Uhrzeit fett, Ereignisarten als Zeilen mit eigenen Farben, gelbe Namensmarkierung
statt Namensliste.
Seit 1.5: Reihenfolge Aktion vor Mannschaft, Timeout mit Ein-TO-Nachfrage,
festes Eingabefenster mit grossem Ziffernblock, 8 Schnellstrafen, Verlauf neueste
Eingabe oben, deutsches OCR-Modell, OCR-Pruefdialoge (Namen, Torwarte, Starting-Goalie).
Bericht/Druck unveraendert ausser zusaetzlicher Timeout-Zeile.

Behoben in 1.7: parseRosterFromTsv verwarf die erste TSV-Zeile als Kopfzeile, obwohl
Tesseract.js keine liefert; verloren ging die Seitenzeile mit der Bildgroesse. Jetzt wird nur
eine echte Kopfzeile ("level...") uebersprungen. Die Schwellwerte des Parsers (Anteile der
Seitenbreite/-hoehe) stammen aus v1.0 und wurden nicht an echten Fotos neu kalibriert:
Erkennung mit einem echten Foto einer eGrep-Mannschaftsmeldung pruefen.

Native Host unveraendert (classes.dex bytegleich zu 1.4 mit gleicher Signatur).
Keine reale Android-VM; Browser-, OCR-Laufzeit-, Druck- und APK-Tests siehe TESTERGEBNISSE.
