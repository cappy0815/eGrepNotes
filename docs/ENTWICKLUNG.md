# eGrep Notes – Entwicklung (Stand 3.3)

Autor: Michael Nowak & KI. Stand: 20.11.2026.
Basis: Quellprojekt 2.9 (Original), darauf 3.0 und 3.1.

## Neu in 3.3 / 3.2 / 3.1 / 3.0

- 3.3: Spielstand bei jedem Tor im Bericht; abgelesene Uhrzeit rechtsbündig.
- 3.2: Spieler-Gedächtnis, EHV-Abgleich, Sicherung, Update-Prüfung, „Bisher“ beim Bearbeiten.
- 3.1: Wischen zwischen Aufstellung, Spiel und Bericht (abschaltbar in den Einstellungen).
- 3.0: Einstellungen mit Heimmannschaft (43 EHV-NRW-Vereine mit Wappen, eigener Name, Neusser EV voreingestellt).

## Neu in 2.9

- Aufstellung auch aus PDF (Text-PDF direkt, gescanntes PDF per Texterkennung).
- Texterkennung fuer lange Aufstellungen (20+ Spieler) deutlich zuverlaessiger; unsichere Nummern gelb markiert.
- "Wer sitzt die Strafe ab?" bei Torwart- und Bankstrafen; Knopf heisst "Bank / Trainer".
- Langer Druck aufs App-Symbol: "Schiri-Zeichen".

## Neu in 2.8

- Schnellmenue in der Kopfzeile: Schiri-Zeichen, Archiv, Info; Link zur Projektseite im Info-Fenster.

## Neu in 2.7

- Penalty (Strafschuss im Spiel) und Notiz als Ereignisarten; Empty-Net-Tore werden automatisch markiert.

## Neu in 2.6

- Lange Vereinsnamen verschieben Tore, Logos und Torhueter nicht mehr; Logos ohne Ring, im Bericht groesser.

## Neu in 2.5

- Schiri-Zeichen jederzeit ueber den Trikot-Knopf in der Kopfzeile; Cross-Check und Haken korrigiert.
- Vereinslogos der EHV-NRW-Mannschaften; Vereinsfarbe als Ring ums Logo.

## Neu in 2.4

- Zeitmodus pro Spiel (Knopf in der Zeile "Bildschirm an lassen", schaltet reihum):
  "Uhr ab" = Restzeit; "Uhr auf" = Hallenuhr laeuft aufwaerts, jedes Drittel ab 0:00;
  "Spielzeit" = durchgehend wie im Spielbericht (zum Nachbauen).
- Schiri-Zeichen mittig in ihren Karten.

## Neu in 2.3

- Schiri-Zeichen: Beschriftung immer vollstaendig lesbar (auch zweizeilig).

## Neu in 2.2

- "Uhr ab / Uhr auf" fuer das ganze Spiel (Zeile "Bildschirm an lassen"): bei "Uhr auf"
  die Spielzeit aus dem DEB-/EHV-Bericht eintippen (2713 = 27:13); Drittel und Restzeit
  rechnet die App aus. Zum Nachbauen von Spielen.
- Bericht zeigt den Bedienernamen mit Stift zum Bearbeiten.
- Versionsnummer im Info-Fenster korrigiert.

## Neu in 2.1

- Strafauswahl als eine Liste, sortiert nach Haeufigkeit in EHV-Spielen (Stichprobe);
  seltene Strafen weiter unten, "Sonstige / eigener Text" am Ende.
- Schalter "Schiri-Zeichen" blendet zu 21 Strafarten das Schiedsrichterzeichen ein
  (Einstellung bleibt auf dem Geraet gespeichert).

## Neu in 2.0

- Strafen 2+2 und 10 Min.; "+ 10 Min." legt aus der Zusammenfassung den zweiten Eintrag an.
- Torwartwechsel mit "Leeres Tor" (Torwart raus / zurueck).
- Penaltyschiessen nach dem 3. Drittel (Knopf unter der Drittelauswahl): Team, Schuetze,
  Treffer ja/nein; Sieger +1 Tor, Endstand "n.P.".
- Archiv der letzten 20 Spiele; "Neues Spiel beginnen" archiviert statt loescht.
- Drittelergebnisse in Bericht/Druck/Text; Hinweis auf moegliches Ueber-/Unterzahltor.
- Eine Verlaengerung ist nicht eingebaut (laut Micha beim EHV nicht vorgesehen; die
  Durchfuehrungsbestimmungen 2026/27 konnten hier nicht automatisch abgerufen werden).

## Neu in 1.9

- Torschuetze, Assists und Strafen per Nummernraster: alle gemeldeten Nummern der
  Mannschaft aufsteigend als Tasten. Beim Tor in der Reihenfolge Schuetze, Assist 1,
  Assist 2 antippen und OK; bei einer Strafe genuegt ein Tap.
- Vertippt? Nummer nochmal antippen. Spieler fehlt? "Andere Nummer" -> Ziffernblock.

## Neu in 1.8

- Texterkennung fuer den echten eGrep-Bogen verbessert: Tabellenlinien werden vor der
  Erkennung entfernt, die Spalten Pos., Nr. und Name werden sauber getrennt, geklammerte
  Nummern und Zusaetze wie "TK"/"GSCMOE" landen nicht mehr im Namen.
- Gemessen an zwei echten Fotos: 33/35 und 29/35 Spieler mit richtiger Nummer und
  Nachname (vorher 19/35 und 21/35). Restfehler sind einzelne Buchstaben.
- Werkzeug tests/tool_real_photos.py zum Nachmessen mit eigenen Fotos (Fotos sind wegen
  personenbezogener Daten NICHT im Projekt enthalten).

## Neu in 1.7

- Texterkennung: Fehlerkorrektur beim Zerlegen des Fotos in Zeilen. Die Bildgroesse geht
  nicht mehr verloren; dadurch werden keine Spieler am Listenende bzw. keine Namensteile
  am rechten Rand mehr abgeschnitten. Mit einem echten Foto noch zu pruefen.
- Komma im Namen gilt nicht mehr als Sonderzeichen.

## Neu in 1.6

- Nach jeder Eingabe erscheint eine grosse Zusammenfassung zum Abschreiben in eGrep:
  Uhrzeit (wie von der Uhr abgelesen) gross oben, darunter Team, Ereignis, Nummer
  (bei Toren auch Assists), Strafe mit Dauer. Das Ereignis ist dabei schon gespeichert.
  OK = fertig, Aendern = zurueck in die Eingabe, Verwerfen = wieder loeschen.
- Im Spielverlauf oeffnet ein Tippen auf einen Eintrag dieselbe Detailansicht
  (Bearbeiten / Schliessen). Die abgelesene Uhrzeit ist groesser und fett.
- "Was ist passiert?": vier Zeilen untereinander, Tor gruen, Strafe orange,
  Torwartwechsel und Timeout grau. Rot/Blau bleiben Heim/Gast vorbehalten.
- Nach dem Foto-Scan werden auffaellige Namen nur in der Aufstellung sanft-gelb markiert
  (mit Grund, z. B. "Ziffern im Namen"). Unbearbeitet werden sie normal verwendet.
  Einmal mit dem Stift oeffnen und speichern entfernt die Markierung.
- Der Spielbericht ist unveraendert.

## Seit 1.5

- Reihenfolge Uhrzeit -> Ereignis -> Mannschaft, Timeout (einer pro Mannschaft),
  festes Eingabefenster mit grossem Ziffernblock, 8 Schnellstrafen, neueste Eingabe oben,
  deutsches OCR-Modell, Torwart-/Starting-Goalie-Nachfrage nach dem Scan.

## Installation und Daten

Paketkennung: de.michaelnowak.egrepnotes
versionCode: 28; versionName: 2.8. Datenformat 9.
Mindestversion Android 8.0 / API 26; targetSdk 28 unveraendert.
Spielnotizen aus 1.4 bis 1.9 werden beim Update unveraendert uebernommen.
WICHTIG: Ein Update ueber 1.4 setzt die Signatur mit dem privaten Schluessel aus
eGrep-Notes-v1.4-PRIVAT.zip voraus. Eine mit anderem Schluessel signierte APK laesst sich
nur nach Deinstallation installieren - dabei gehen die Spielnotizen auf dem Handy verloren.
Keine neuen Berechtigungen, keine neuen Serverdienste. Speicherung lokal in der App.

## Vollstaendiger Offline-Build

Benoetigt: Python 3.10+ und OpenSSL im PATH.

    python build_apk.py --signing-dir PFAD/ZU/signing --output dist/eGrep-Notes-v2.8.apk

--init-signing NICHT fuer ein Update verwenden: es erzeugt eine andere Identitaet.

## Tests

    node tests/test_logic.js
    node tests/test_penalty_duration.js
    node tests/test_parser.js
    node tests/test_goalie_parser.js
    node tests/test_v15_logic.js
    node tests/test_v16_logic.js
    node tests/test_v17_logic.js
    node tests/test_v18_logic.js
    node tests/test_v20_logic.js
    python tests/test_apk.py dist/eGrep-Notes-v2.8.apk
    python tests/test_upgrade.py eGrep-Notes-v2.7.apk dist/eGrep-Notes-v2.8.apk

Browser-Tests benoetigen Python Playwright und Chromium (CHROMIUM=Pfad, sonst
/usr/bin/chromium oder /opt/pw-browsers/chromium). PDF-Pruefung mit PyMuPDF oder,
falls nicht vorhanden, poppler-utils:

    python tests/test_ui.py /tmp/egrep-ui
    python tests/test_period_ui.py /tmp/egrep-period
    python tests/test_operator_photo_ui.py /tmp/egrep-operator
    python tests/test_penalty_ui.py /tmp/egrep-penalties
    python tests/test_v15_ui.py /tmp/egrep-v15
    python tests/test_v16_ui.py /tmp/egrep-v16
    python tests/test_v19_ui.py /tmp/egrep-v19
    python tests/test_v20_ui.py /tmp/egrep-v20
    python tests/test_ocr_runtime.py /tmp/egrep-ocr
    python tests/test_print.py /tmp/egrep-print

Ergebnisse und Grenzen siehe TESTERGEBNISSE.txt. Nicht getestet: echtes Handy,
Installation, Kamera, echtes Foto einer Mannschaftsmeldung, Systemdruckdialog.
