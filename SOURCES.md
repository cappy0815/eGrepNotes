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

## Vereinsliste und Wappen fuer die Heimmannschaft (3.0)

https://www.ehv-nrw.de/club/clublist/ - abgerufen 20.11.2026
Mitgliedsvereine des EHV NRW mit Kurzname, vollem Vereinsnamen und Wappen (43 Eintraege). Die Wappen
wurden auf 96 px verkleinert und als WebP in assets/clubs.js eingebettet. Die Wappen sind Marken der
jeweiligen Vereine. Neusser EV nutzt weiter das mitgelieferte nev-logo.png.

## PDF-Import (2.9)

https://www.npmjs.com/package/pdfjs-dist - Version 3.11.174, legacy build, Apache 2.0.
Sicherheitshinweis CVE-2024-4367: Dokumente werden mit isEvalSupported:false geoeffnet.
