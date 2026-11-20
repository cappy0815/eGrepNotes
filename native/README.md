# Nativer Android-Teil

`classes.dex` ist der Android-Host von eGrep Notes 2.9, unveraendert uebernommen (SHA-256 siehe unten).
Er laedt die Oberflaeche aus `assets/index.html` in eine WebView und stellt bereit:
Kamera und Galerie (Foto/PDF), Drucken (A4), Bildschirm-an waehrend des Spiels, Zurueck-Taste,
Link nur zu https://cappy0815.github.io/ und die App-Verknuepfung "Schiri-Zeichen"
(langer Druck aufs App-Symbol, startet `index.html#signs`).

Der urspruengliche Generator (von Hand erzeugter Bytecode) ist nicht mehr vorhanden. `decompiled/`
enthaelt eine mit androguard erzeugte Lesefassung der vier Klassen. Sie dient nur zum Nachlesen und ist
nicht als baubarer Quelltext geprueft.

Geprueft wird der Host mit `tests/test_native_camera.py` (kleiner Dex-Interpreter mit simulierten
Android-APIs, kein echtes Geraet).

SHA-256 classes.dex: `4ceb820c554cb252c5ce55c7abcb12f9271afbc1bab97396ab24dd9dcfee5594`
