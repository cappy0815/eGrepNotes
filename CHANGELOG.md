# Changelog eGrep Notes

Hinweis: Die Eintraege 1.5 bis 2.8 wurden am 20.11.2026 aus Projektnotizen rekonstruiert, weil der
damalige Arbeitsordner verloren ging. Inhaltlich gepruefte Stellen sind wie damals formuliert; wo
Details fehlen, steht das dabei.

## 3.0 - 2026-11-20

- Einstellungen im Menue (drei Striche): Heimmannschaft waehlen. Liste der Mitgliedsvereine des
  EHV NRW mit Wappen (43 Vereine, offline in der App), Suchfeld (Umlaute egal, auch voller
  Vereinsname). Fehlt ein Verein: eigenen Namen eintragen (dann neutrales Wappen).
- Neusser EV bleibt Voreinstellung; "Zurueck auf Neusser EV" stellt sie wieder her.
- Die Heimmannschaft bestimmt Wappen in Kopfzeile, Info, Bericht und Ausdruck sowie den
  Heimnamen neuer Spiele. Ein leeres Spiel uebernimmt den Namen sofort, ein laufendes Spiel
  behaelt seine Mannschaften.
- Farben bleiben fuer alle Vereine gleich (Rot = Heim, Blau = Gast), bewusst so entschieden.
- Quellprojekt neu aufgebaut und auf GitHub (cappy0815/eGrepNotes). Der native Android-Teil wird
  seitdem als fertige Binaerdatei aus 2.9 uebernommen (native/README.md); Manifest, Ressourcen
  und Oberflaeche erzeugt das Build-Skript. Geprueft: Aus den 2.9-Dateien entsteht inhaltlich
  exakt die veroeffentlichte 2.9-APK.

## 2.9 - 2026-11-15

- Aufstellung aus PDF: Das Feld heisst jetzt "Foto oder PDF". PDFs mit Text (z. B. aus eGrep
  gespeichert) werden direkt gelesen, ohne Texterkennung (unter 1 s). Gescannte PDFs (nur Bild)
  laufen ueber die Texterkennung. Gelesen wird Seite 1. pdf.js wird erst beim ersten PDF geladen.
- Texterkennung fuer lange Aufstellungen (20+ Spieler je Team): kein fester Schnitt mehr nach
  unten; jede Mannschaft endet an ihrer eigenen Trainer-/Betreuerzeile. Zweiter Durchgang nur
  fuer die Spalten Pos./Nr. (nur Ziffern), einzelne Zellen ohne erkannte Nummer werden gezielt
  nachgelesen. Weichen beide Durchgaenge ab, wird der Spieler gelb markiert
  ("Nummer pruefen: 23 oder 29?"). Grenze zwischen Heim- und Gasttabelle aus dem Spaltenkopf.
- Torwart-Erkennung: Ein "G" unterhalb eines Spielers mit klar gelesener Feldposition
  (D, F, LD, ...) gilt nicht mehr als Torwart (falsch gelesenes C/D).
- "Wer sitzt die Strafe ab?" bei Strafen gegen einen Torwart (in der Aufstellung als TW oder
  laut Torwartwechsel im Tor) und bei Bankstrafen: Nummernraster ohne Torwarte,
  "Andere Nummer" oder "Spaeter eintragen" ("Absitzender offen"). Anzeige in Zusammenfassung,
  Verlauf, Bericht, Druck und Text. Bei "+10 Min." als zweitem Eintrag bleibt er offen.
- Knopf "Bankstrafe / Team" heisst "Bank / Trainer".
- App-Verknuepfung: Langer Druck auf das App-Symbol zeigt "Schiri-Zeichen".

## 2.8 - 2026-11-13

- Schnellmenue in der Kopfzeile (Knopf mit drei Strichen) statt Trikot- und Info-Knopf:
  Schiri-Zeichen, Archiv (mit Anzahl) und Info, auf jedem Reiter. Antippen daneben oder die
  Zurueck-Taste schliesst das Menue. Der Archiv-Knopf im Bericht bleibt.
- Info-Fenster: antippbarer Link zur Projektseite cappy0815.github.io (oeffnet den Browser).
  Nur genau diese Adresse darf die App verlassen; alle anderen Links bleiben gesperrt.

## 2.7 - 2026-11-08

- Neue Ereignisart "Penalty" (Strafschuss waehrend des Spiels): Mannschaft, Schuetze (Raster
  oder Tastatur), Tor / kein Tor. Ein verwandelter Penalty zaehlt als Tor (Spielstand,
  Drittelstand). Kein Ueberzahl-Hinweis bei Penaltys.
- Neue Ereignisart "Notiz": freier Text (max. 300 Zeichen) mit Uhrzeit, fuer eine Mannschaft
  oder "Allgemein". Erscheint in Verlauf, Bericht, Druck und Text.
- Empty-Net-Tor: Ein Tor, waehrend beim Gegner laut Torwartwechsel "leeres Tor" eingetragen ist,
  wird markiert (Verlauf "Empty Net", Zusammenfassung, Bericht/Druck "EN", Text "Tor (EN)").
- Ereignisart-Auswahl: Tor und Strafe volle Breite, darunter je zwei Knoepfe
  (Torwartwechsel | Timeout, Penalty | Notiz).

## 2.6 - 2026-11-02

- Lange Vereinsnamen verschieben nichts mehr: Anzeigetafel als gemeinsames Raster fuer beide
  Teams; Namen auf der Tafel hoechstens zwei Zeilen.
- Logos ohne Farbring; im Bericht 40 px neben dem Ergebnis.

## 2.5

- Vereinslogos der EHV-NRW-Mannschaften (hockeydata, offline) auf Tafel und im Bericht.
- Uebersicht aller Schiri-Zeichen; Zeichen fuer Cross-Check und Haken korrigiert.

## 2.4

- Drei Zeitmodi pro Spiel: Uhr laeuft ab, Uhr laeuft auf (Hallenuhr, jedes Drittel ab 0:00),
  Spielzeit 0:00 bis 60:00.
- Schiri-Bilder mittig in ihren Kaesten.

## 2.3

- Beschriftung der Schiri-Zeichen vollstaendig lesbar (zweizeilig).

## 2.2

- Bedienername im Bericht, Versionsnummer im Info-Fenster, Zeitmodus fuer das ganze Spiel.

## 2.1

- Strafen nach Haeufigkeit in EHV-Spielen sortiert (Stichprobe 27 Spiele, Okt. 2026),
  Strafauswahl als scrollbare Liste, Schiri-Zeichen einblendbar.

## 2.0

- Strafmass 2+2 und 10 ("+10" als zweiter Eintrag), leeres Tor, Penaltyschiessen, Archiv der
  letzten 20 Spiele, Drittelergebnisse, Hinweis auf moegliche Ueber-/Unterzahltore.

## 1.9

- Nummernraster fuer Tor und Strafe (Torschuetze, Assists), Ziffernblock als Ausweg.

## 1.5 bis 1.8

- Texterkennung mit deutschem Sprachmodell (ab 1.5) und fuer echte eGrep-Boegen (1.8:
  Tabellenlinien entfernen, Spaltengrenzen aus den Koepfen). Weitere Details nicht erhalten.

## 1.4 - 2026-10-08

- Strafmass 2/5/Spieldauer als zusaetzliches persistentes Ereignisfeld.
- 2 Minuten nur fuer NEUE Eintraege voreingestellt, historische Strafen nicht geraten.
- Namen in Berichtansicht, Dauer in Verlauf, Bericht, Text und Druck.
- Heim rot/blassrot und Gast blau/blassblau, Typ/Team zusaetzlich als Text.
- Gemessene A4-Einseitenanpassung, keine geloeschten oder abgeschnittenen Eintraege.
- Option lesbare Mehrseitenausgabe; Warnung unter 6.5 pt.
- Android-Druckjob mit A4 und 12.7-mm-Raendern; neue native Tests.
- Quellprojekt, private Signiersicherung und Wiederherstellungsbuild.

## 1.3 - 2026-10-07

- Restuhrzeit grau mit groesserer Schrift im Verlauf, Bericht und Druck.
- Eigene Kameraaktion mit vollstaendiger Bilddatei und privatem URI-Provider.
- Abbruch, fehlende Kamera, leere Resultate und Activity-Wiederherstellung behandelt.
- Optionaler Bedienername einmal pro Spiel, spaeter editierbar und in allen Ausgaben.
- Bediener bleibt bei Rueckgaengig unveraendert, wird bei Spiel-Reset geloescht.
- Native Builder-Kamera-Tests und Bediener-/Foto-/Druckregressionen ergaenzt.

# 1.2 - 07.10.2026

- Aktuelles Drittel persistent; initial/reset ohne Auswahl.
- Neue Ereignisse erben das aktuelle Drittel; kein wiederholtes Auswählen.
- Zeitfenster zeigt das Drittel; lokale Abweichung für Nachträge möglich.
- Höhere Restzeit: ausdrückliche Wahl zwischen Drittelbeginn, Nachtrag, Korrektur.
- Kein mehrfaches Nachfragen für dieselbe bestätigte Zeitabweichung.
- Bearbeiten und Undo verstellen die aktive Drittelauswahl nicht.
- Beschriftete Rückgängig-Schaltfläche statt alleinstehendem Pfeil.
- Versionscode 12, Paketkennung und Signierzertifikat von 1.1 erhalten.

Keine Änderung am nativen Host, an der OCR oder an den bisherigen Spielregeln.
