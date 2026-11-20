# Quellen und Abgrenzung - Abruf 07.10.2026

## Android-Funktionen

https://developer.android.com/develop/background-work/background-tasks/awake/screen-on
Dokumentiert Keep-Screen-On in einer sichtbaren Activity/View und das normale
Abschalten, sobald die App in den Hintergrund wechselt.

https://developer.android.com/training/monitoring-device-state/battery-monitoring
Dokumentiert den Sticky-Broadcast ACTION_BATTERY_CHANGED und EXTRA_PLUGGED.
In unserem Host wird registerReceiver(null, filter) nur zur Abfrage verwendet;
es wird kein dauerhafter BroadcastReceiver registriert.

## Strafenkurzliste

https://regelbuch.del-refs.de/web/2026-27/
Aktuelles DEL-Schiedsrichterregelbuch: Kategorien u. a. Boarding, Charging,
Checking from Behind, Clipping, Elbowing, Fighting, Head-butting, Kicking,
Kneeing, Roughing, Slew-footing, Throwing Equipment, Holding, Hooking,
Interference, Tripping, Butt-ending, Cross-checking, High-sticking, Slashing,
Spearing, Delaying the Game, Diving/Embellishment und Too Many Players.

https://www.deb-online.de/strafbank/
Beispiele für deutschsprachige Begriffe Stockcheck, Stockstich, Bandencheck,
Check gegen Kopf/Nacken, Slewfooting und Unsportliches Verhalten.

https://www.adler-kids.de/udos-welt/udos-eishockey-guide/strafen/
Ergänzend nur die Liste gebräuchlicher deutschen Foulbezeichnungen verwendet.
Dort aufgeführte Strafzeiten/Strafarten wurden NICHT als aktuelle Vorschrift
übernommen.

Die App-Liste ist eine eigene, verkürzte Notiz-Auswahl. Keine vollständige
amtliche eGrep-Codeliste, keine Regeln zur Strafdauer und keine automatische
Schiedsrichterentscheidung. DEL-spezifische Regeln werden nicht auf NRW-
Jugendspiele übertragen. Die tatsächliche Ansage kann über Sonstige erfasst
werden. Das Strafmaß wird nicht automatisch berechnet.

## Logos und OCR

https://ehv-nrw.de/club/clublist/
Die Vereinsliste wurde für den Bonuswunsch angesehen. Weitere Vereinslogos
wurden in dieser Ausgabe noch nicht eingebunden. Das NEV-Logo stammt aus
dem vom Nutzer gelieferten und im v1.0-Projekt enthaltenen Asset.

Tesseract.js, Worker, WASM-Kern und englisches Sprachmodell wurden aus dem
funktionierenden v1.0-Quellprojekt übernommen. Lizenzhinweise siehe
THIRD_PARTY_NOTICES.md und APACHE-2.0.txt.

## Update 1.2 - technische Referenzen, Abruf 07.10.2026

https://developer.mozilla.org/en-US/docs/Web/API/Window/localStorage
Speicher-API; Wiederherstellung des gewählten Drittels wird im vorhandenen
App-Zustand implementiert. Native Speicherung auf dem Handy noch zu testen.

https://developer.android.com/studio/publish/app-signing
Update-Signierung. Paketkennung und tatsächliche Zertifikate der APKs
1.1/1.2 wurden zusätzlich direkt aus den APK-Dateien verglichen.

## Kamera-Update 1.3 (07.10.2026)

- Android Camera Intents: https://developer.android.com/media/camera/camera-intents
- WebChromeClient.FileChooserParams (createIntent/isCaptureEnabled/parseResult): https://developer.android.com/reference/android/webkit/WebChromeClient.FileChooserParams
- ContentProvider openFile: https://developer.android.com/reference/android/content/ContentProvider
- Android MediaStore ACTION_IMAGE_CAPTURE / EXTRA_OUTPUT: https://android.googlesource.com/platform/frameworks/base/+/refs/heads/android10-mainline-media-release/core/java/android/provider/MediaStore.java

Keine neue OCR-Bibliothek; vorhandene Tesseract-Assets unveraendert. Kamera-
Vollbildpfad benoetigt EXTRA_OUTPUT; der Rueckgabe-Intent darf null sein.

## Druck und Strafmass 1.4 - Abruf 08.10.2026

https://developer.android.com/training/printing/html-docs
WebView-Druckadapter und Grenzen von HTML-Druck auf Android. Native Ausloesung
ueber die bestehende lokale URL-Bruecke, nicht allein ueber window.print.

https://developer.mozilla.org/en-US/docs/Web/API/Window/beforeprint_event
Vorbereitung der Druckansicht. Die App bereitet den Druck zusaetzlich explizit
VOR dem nativen Aufruf vor; sie verlaesst sich nicht auf dieses Browserereignis.

Die Auswahl 2 Minuten, 5 Minuten, Spieldauer stammt direkt vom Nutzerauftrag.
Sie ist KEINE Behauptung einer vollstaendigen offiziellen Strafmass-Codeliste.
Es werden keine Regeln oder Spieldauer-Minuten aus Quellen hinzuerfunden.

## Update 1.5 - 18.10.2026

https://github.com/tesseract-ocr/tessdata_fast (Commit 87416418657359cb625c412a48b6e1d6d41c29bd)
deu.traineddata, 1 525 436 Bytes, SHA-256
19d219bbb6672c869d20a9636c6816a81eb9a71796cb93ebe0cb1530e2cdb22d. Lizenz Apache 2.0.
Herkunftspruefung: Das bisher eingebettete eng.traineddata ist bytegleich mit
tessdata_fast/eng.traineddata (SHA-256 7d4322bd...170b2). Das deutsche Modell stammt
daher aus derselben Modellreihe und passt zum vorhandenen LSTM-Kern.
Komprimiert (gzip -9 -n) als tessdata/deu.traineddata.gz, 853 415 Bytes.

Timeout: "nur ein Timeout pro Mannschaft" ist eine Vorgabe des Nutzers.
Die App fragt bei einem zweiten Timeout nach und sperrt NICHT (Korrekturen bleiben moeglich).

Namenspruefung nach OCR: eigene Heuristik (Ziffern, Sonderzeichen, einzelnes Wort,
einzelne Buchstaben, Woerter ohne Vokal, lange Konsonantenketten, drei gleiche Zeichen,
sehr lang). Keine Quelle, kein Namensverzeichnis. Umlaute werden nach Nutzervorgabe
nicht bewertet. Die App aendert nichts ohne Antwort des Bedieners.

Strafen-Reihenfolge (2.1): Stichprobe aus 27 Spielberichten des EHV NRW ueber die
hockeydata-Schnittstelle, die auch die EHV-Live-App nutzt (Abruf Okt. 2026). Gezaehlt wurden
241 Strafen mit Dauer > 0 nach Strafcode (TRIP 56, HOOK 25, CHARG 24, HOLD 19, SLASH 18,
ROUGH 17, BOARD 14, INTRF 12, CROSS 12, UN-SP 7, FIGHT/FISTI 6, HI-ST 5, KNEE 4, GA-MI 3,
TOO-M 3, DELAY 3, je 2: SPEAR, MISC, ELBOW, CHE-H; je 1: CRITIC, CLIP, MATCH, EQ-INF, CH-PL).
Die Zuordnung der Codes zu den deutschen Bezeichnungen der App ist eine eigene Zuordnung;
GA-MI, MATCH, CRITIC und CH-PL sind nicht zugeordnet (Rueckfrage beim Nutzer offen).
Stichprobe, keine Vollerhebung.

Schiri-Zeichen (2.1): Figuren aus dem vom Nutzer bereitgestellten, ueberarbeiteten
Zeichenblatt (per Chat, zur Nutzung freigegeben). Beschriftungen, Codes und Farbmarken
wurden entfernt; die Zuordnung zur Strafart folgt der Beschriftung des Blattes.
"Stockhalten": nur die linke Figur. Faustkampf nutzt das Zeichen "Uebertriebene Haerte".

Vereinslogos (2.5): hockeydata team-logos (https://api.hockeydata.net/img/icehockey/ebel/team-logos/<id>.png),
dieselbe Quelle, die ehv-nrw.de und EHV Live nutzen. Abgerufen 02.11.2026 fuer alle Mannschaften der
28 EHV-NRW-Ligen (264 Team-IDs, 262 mit Logo, 98 verschiedene Bilder). Die Logos sind Marken der
jeweiligen Vereine; Nutzung hier nur zur Anzeige in der privaten Notiz-App. Akzentfarbe = haeufigste
kraeftige Farbe im Logo (automatisch ermittelt, keine offizielle Vereinsfarbe).

Schiri-Zeichen (2.5): Cross-Check und Haken nach dem Original-Zeichenblatt (eishockeyregeln.ch, vom
Nutzer bereitgestellt) korrigiert. Beschreibungen geprueft: "Cross-Checking: forward motion with both
fists clenched, extending from the chest"; "Hooking: tugging motion with both arms, as if pulling
something toward the stomach" (AIHA Penalty Signals; Sheffield Hallam Univ., Referee signals).
Cross-Check: linke Bildhaelfte gespiegelt (beide Faeuste vorn); Haken: Schlaeger entfernt.

## Vereinsliste und Wappen fuer die Heimmannschaft (3.0)

https://www.ehv-nrw.de/club/clublist/ - abgerufen 20.11.2026
Mitgliedsvereine des EHV NRW mit Kurzname, vollem Vereinsnamen und Wappen (43 Eintraege), auf 96 px
verkleinert, als WebP in assets/clubs.js. Neusser EV nutzt weiter das mitgelieferte nev-logo.png.

## EHV-Abgleich (3.2)

https://ehv-nrw.de/leagues/next-games/ - enthaelt den oeffentlichen hockeydata-Schluessel und die Liga-Kennungen
(wie im EHV-Live-Ticker genutzt). Datenquelle https://api.hockeydata.net/data/ebel/Schedule und GetGameReport
(am 20.11.2026 geprueft: Aufstellungen homeFieldPlayers/homeGoalKeepers/awayFieldPlayers/awayGoalKeepers mit
Nummer und Name; teils schon vor dem Spiel). Genutzt werden nur Nummer, Name, Torwart.

## Sicherung (3.2)

https://developer.android.com/training/data-storage/shared/documents-files - Intent ACTION_CREATE_DOCUMENT
(CATEGORY_OPENABLE, EXTRA_TITLE) und ContentResolver.openOutputStream fuer das Schreiben der Datei.
