## 3.3 - 2026-11-23

- Bericht, Ausdruck und Text: Bei jedem Tor steht der Spielstand nach dem Tor (z. B. "Tor 2:1"),
  in Spielzeit-Reihenfolge. Verwandelte Penaltys zaehlen mit, verschossene nicht.
- Die graue abgelesene Uhrzeit steht in Bericht und Ausdruck rechtsbuendig in der Zeitspalte.
- Strafen in Bericht und Ausdruck zweizeilig: "Strafe #Nummer Name", darunter "Strafmass · Strafart"
  (und ggf. wer absitzt).

## 3.2 - 2026-11-20

- Beim Bearbeiten steht oben "Bisher: Zeit · Art · Mannschaft · Nummern/Strafe"; die bisherige
  Auswahl ist in jedem Schritt markiert (Ereignisart, Mannschaft, Nummern, Strafart, Strafmass).
- Spieler-Gedaechtnis (nur auf dem Geraet): lernt bei "Neues Spiel" die Aufstellungen beider
  Mannschaften (nur Spieler ohne offene Markierung), getrennt nach Mannschaft und Altersklasse
  (aus der Spielnummer, z. B. U13). Nach dem Einlesen und per Knopf "Spieler abgleichen" kommen
  Vorschlaege: Schreibweise (z. B. Schloeber -> Schloesser), Nummer (23 -> 29), Torwart.
  Nichts wird ohne Bestaetigung geaendert; einzelne Vorschlaege abwaehlbar; Rueckgaengig moeglich.
- EHV-Abgleich (abschaltbar): sucht das Spiel ueber die Spielnummer in den EHV-Spielplaenen
  (hockeydata, wie ehv-nrw.de). Steht dort schon die Aufstellung dieses Spiels, wird damit
  verglichen (inkl. fehlender Spieler zum Ergaenzen), sonst mit den letzten Spielen der
  Mannschaften. Spielplaene werden 6 Stunden zwischengespeichert. Gemerkt werden nur Nummer,
  Name und Torwart, keine Geburtsdaten.
- Sicherung: "Sicherung speichern" schreibt aktuelles Spiel, Archiv, Spieler-Gedaechtnis und
  Einstellungen als JSON-Datei (Android-Dialog "Speichern unter"). "Sicherung einlesen" fuehrt
  zusammen und loescht nichts; ein laufendes Spiel kommt vorher ins Archiv.
- Update-Pruefung wie in den anderen Apps: Versionsdatei auf cappy0815.github.io, einmal taeglich
  automatisch (abschaltbar) oder per "Jetzt pruefen"; Hinweis im Menue, Download oeffnet den Browser.
  Installiert wird nichts automatisch.
- Neue Berechtigung INTERNET (nur fuer Update-Pruefung und EHV-Abgleich). Links in den Browser
  jetzt fuer alle Seiten unter https://cappy0815.github.io/ (Projektseite, Download).

## 3.1 - 2026-11-20

- Wischen zwischen Aufstellung, Spiel und Bericht: nach links = naechster Reiter, nach rechts =
  vorheriger. Kurze, langsame oder schraege Bewegungen (Scrollen), Eingabefelder und offene
  Fenster loesen nichts aus. Abschaltbar in den Einstellungen ("Bedienung").

## 3.0 - 2026-11-20

- Einstellungen im Menue (drei Striche): Heimmannschaft waehlen. Liste der Mitgliedsvereine des
  EHV NRW mit Wappen (43 Vereine, offline in der App), Suchfeld (Umlaute egal, auch voller
  Vereinsname). Fehlt ein Verein: eigenen Namen eintragen (dann neutrales Wappen).
- Neusser EV bleibt Voreinstellung; "Zurueck auf Neusser EV" stellt sie wieder her.
- Die Heimmannschaft bestimmt Wappen in Kopfzeile, Info, Bericht und Ausdruck sowie den
  Heimnamen neuer Spiele. Ein leeres Spiel uebernimmt den Namen sofort, ein laufendes Spiel
  behaelt seine Mannschaften.
- Farben bleiben fuer alle Vereine gleich (Rot = Heim, Blau = Gast), bewusst so entschieden.
- Quellprojekt auf GitHub (cappy0815/eGrepNotes).

## 2.9 - 2026-11-15

- Aufstellung aus PDF: Das Feld heisst jetzt "Foto oder PDF". PDFs mit Text (z. B. aus eGrep
  gespeichert) werden direkt gelesen, ohne Texterkennung (unter 1 s). Gescannte PDFs (nur Bild)
  laufen ueber die Texterkennung. Gelesen wird Seite 1. pdf.js wird erst beim ersten PDF geladen.
- Texterkennung fuer lange Aufstellungen (20+ Spieler je Team): kein fester Schnitt mehr nach
  unten; jede Mannschaft endet an ihrer eigenen Trainer-/Betreuerzeile. Zweiter Durchgang nur
  fuer die Spalten Pos./Nr. (nur Ziffern), einzelne Zellen ohne erkannte Nummer werden gezielt
  nachgelesen. Weichen beide Durchgaenge ab, wird der Spieler gelb markiert
  ("Nummer pruefen: 23 oder 29?"). Grenze zwischen Heim- und Gasttabelle aus dem Spaltenkopf
  statt fest bei 46 %.
- Torwart-Erkennung: Ein "G" unterhalb eines Spielers mit klar gelesener Feldposition
  (D, F, LD, ...) gilt nicht mehr als Torwart (falsch gelesenes C/D).
- "Wer sitzt die Strafe ab?": Bei einer Strafe gegen einen Torwart (in der Aufstellung als TW
  markiert oder laut Torwartwechsel gerade im Tor) und bei Bankstrafen fragt die App nach dem
  Spieler, der absitzt: Nummernraster ohne Torwarte, "Andere Nummer" oder "Spaeter eintragen"
  (dann "Absitzender offen" markiert). Anzeige in Zusammenfassung, Verlauf, Bericht, Druck und
  Text. Bei "+10 Min." als zweitem Eintrag bleibt der Absitzende offen.
- Knopf "Bankstrafe / Team" heisst jetzt "Bank / Trainer".
- App-Verknuepfung: Langer Druck auf das App-Symbol zeigt "Schiri-Zeichen" und oeffnet direkt
  die Uebersicht. Laeuft die App schon, bleibt das Spiel offen (kein Neustart).

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
  Torwart rausnehmen ging schon seit 2.0 (Torwartwechsel -> "Leeres Tor").
- Ereignisart-Auswahl: Tor und Strafe volle Breite, darunter je zwei Knoepfe
  (Torwartwechsel | Timeout, Penalty | Notiz); passt weiter ohne Scrollen.

## 2.6 - 2026-11-02

- Lange Vereinsnamen verschieben nichts mehr: Anzeigetafel als gemeinsames Raster fuer beide
  Teams (Namen / Logo + Tore / "Im Tor" je in einer Zeile). Namen auf der Tafel hoechstens zwei
  Zeilen (sonst "..."), im Bericht immer vollstaendig.
- Bericht: Logos und Ergebnis in einer Zeile, Namen darunter; Logos etwas groesser (40 px).
- Kein Farbring mehr um die Logos (weisser Kreis auf der dunklen Tafel bleibt).

## 2.5 - 2026-11-02

- Schiri-Zeichen jederzeit aufrufbar: Knopf (Trikot-Symbol) in der Kopfzeile, auf jedem
  Reiter. Alle 21 Zeichen nach Haeufigkeit, antippen vergroessert, Zurueck schliesst.
- Zeichen korrigiert nach dem Original (eishockeyregeln.ch) und Regel-Beschreibungen:
  Cross-Check = beide Faeuste vor der Brust nach vorn, ohne Schlaeger;
  Haken = Ziehbewegung mit beiden Armen, ohne Schlaeger.
- Vereinslogos der EHV-NRW-Mannschaften (98 Logos, offline in der App): Teamauswahl,
  Anzeigetafel (neben der Torzahl), Bericht und Druck. Zuordnung ueber den Teamnamen, auch
  mit Altersklasse (z. B. "Krefelder EV U15 A"). Unbekannter Verein: Initiale wie bisher.
  Vereinsfarbe nur als Ring ums Logo; Rot = Heim / Blau = Gast bleiben.

## 2.4 - 2026-10-24

- Drei Zeitmodi pro Spiel, Knopf schaltet reihum:
  "Uhr ab" (Restzeit, wie bisher), "Uhr auf" (Hallenuhr laeuft aufwaerts und beginnt jedes
  Drittel bei 0:00; Drittel waehlen wie bei "Uhr ab"), "Spielzeit" (durchgehend 0:00-60:00
  wie im DEB-/EHV-Spielbericht; das war "Uhr auf" in 2.2/2.3).
  Bei "Uhr auf" fragt die App bei einer KLEINEREN Zeit als beim letzten Eintrag
  "Neues Drittel oder Nachtrag?". Verlauf, Zusammenfassung, Bericht, Druck und Text zeigen
  dann die abgelesene Hallenuhr. Intern weiter Drittel + Restzeit.
  Gespeicherte Spiele mit "Uhr auf" aus 2.2/2.3 oeffnen als "Spielzeit".
- Schiri-Zeichen: Bild und Beschriftung sitzen mittig in der Karte (vorher bis zu 50 px nach
  links versetzt; Ursache: Rasterspalte nur so breit wie der Inhalt).

## 2.3 - 2026-10-19

- Schiri-Zeichen: Karten wachsen mit der Beschriftung; zweizeilige Namen (z. B. "Unkorrekter
  Koerperangriff") ragten bisher ueber den Kartenrand und waren nicht lesbar. Bilder mit fester
  Groesse (108 px, auf kleinen Bildschirmen 92 px).

## 2.2 - 2026-10-19

- Zeiteingabe fuer das ganze Spiel umschaltbar: Knopf "Uhr ab / Uhr auf" in der Zeile
  "Bildschirm an lassen". "Uhr auf" = Spielzeit wie im DEB-/EHV-Spielbericht (z. B. 2713 =
  27:13). Das Drittel ergibt sich aus der Zeit (20:00 = Ende 1. Drittel), die App rechnet
  die Restzeit aus (27:13 -> 2. Drittel, Uhr 12:47). Zusammenfassung zeigt dann die Spielzeit
  gross. Bei frueheren Zeiten nur "Nachtrag" (kein Drittelwechsel). Gespeichert wird weiter
  Drittel + Restzeit, daher keine Datenumstellung. Einstellung gehoert zum Spiel (Archiv
  behaelt sie, neues Spiel startet mit "Uhr ab"; Rueckgaengig aendert sie nicht).
  Bericht/Druck vermerken "Erfasst als Spielzeit".
- Bericht: statt "Bedienernamen bearbeiten" steht der Name mit Stift zum Bearbeiten.
- Info-Fenster: Versionsnummer kommt aus der App-Logik (stand faelschlich auf 2.0).

## 2.1 - 2026-10-19

- Strafauswahl: alle Strafarten in EINER Liste, sortiert nach Haeufigkeit aus einer
  Stichprobe von 27 EHV-NRW-Spielen (241 Strafen): Beinstellen, Haken, Unkorrekter
  Koerperangriff, Halten, Stockschlag, Uebertriebene Haerte, Bandencheck, ...
  Strafarten ohne Vorkommen danach, "Sonstige / eigener Text" am Ende.
  Die Liste scrollt innerhalb des Eingabefensters; die Strafmass-Leiste bleibt stehen.
  Die bisherige Auswahlliste "Weitere Strafen" entfaellt.
- Schalter "Schiri-Zeichen": zeigt zu 21 Strafarten das Schiedsrichterzeichen als Bild
  (Figuren aus Michas ueberarbeitetem Zeichenblatt, ohne Text). Die Einstellung merkt sich
  das Geraet. Strafarten ohne Zeichen sind als "kein Zeichen" markiert.
- Beim Bearbeiten ist die gespeicherte Strafart in der Liste markiert.
- EHV: keine Verlaengerung (vom Nutzer geprueft) - Spielende nach 3 Dritteln bzw. Penaltyschiessen.

## 2.0 - 2026-10-19

- Strafmass 2+2 Min. und 10 Min. (Disziplinarstrafe). 10 Min. als ZWEITER Eintrag mit
  gleicher Zeit und Nummer (wie in eGrep): Knopf "+ 10 Min." direkt in der Zusammenfassung
  einer 2-, 2+2- oder 5-Minuten-Strafe; bei Auswahl "10 Min." eigener Speichern-Knopf.
  Strafmass-Leiste in zwei Zeilen, deutlicher markiert.
- Torwartwechsel mit "Leeres Tor": Torwart raus fuer einen Feldspieler und zurueck
  (Rueckkehr schlaegt den Torwart vor, der rausgegangen ist). "Im Tor: Leeres Tor".
- Penaltyschiessen: Team, Schuetze (Raster/Nummer/ohne Nummer), Treffer oder nicht.
  Mannschaften wechseln automatisch ab. Nur der Sieger bekommt +1 Tor, Endstand mit "n.P.".
  Versuche antippen zum Loeschen. Im Verlauf, Bericht, Text und Druck.
- Archiv: "Neues Spiel beginnen" legt das alte Spiel ins Archiv (letzte 20, nur auf dem
  Geraet). Oeffnen holt ein Spiel zurueck (z. B. erneut drucken), Loeschen mit Rueckfrage.
- Drittelergebnisse im Bericht, Druck und Text ("Drittel: 1:0 · 2:1 · 0:0").
- Hinweis in der Zusammenfassung eines Tores, wenn laut Eintraegen eine Strafe laeuft:
  "Moegliches Ueberzahltor / Unterzahltor?" (nur Hinweis, keine Regelentscheidung).
- Datenformat 9 (Penaltyschiessen, leeres Tor). Daten aus 1.x werden uebernommen.

## 1.9 - 2026-10-19

- Nummernraster statt Zifferntippen (wie in eGrep): nach der Mannschaft erscheinen alle
  gemeldeten Nummern aufsteigend (Torwarte mit "TW", darunter der Nachname).
  Tor: Reihenfolge der Taps = Schuetze, Assist 1, Assist 2 (Anzeige T/A1/A2), dann OK.
  Nochmal tippen nimmt eine Nummer heraus, die folgenden ruecken nach; hoechstens drei.
  Strafe: ein Tap -> direkt zur Strafart; "Bankstrafe / Team" im Raster.
- "Andere Nummer" oeffnet den bisherigen Ziffernblock (z. B. Spieler nicht erkannt).
  Ohne Aufstellung oder bei Nummern ausserhalb der Aufstellung (Bearbeiten) kommt
  direkt der Ziffernblock. Torwartwechsel unveraendert.

## 1.8 - 2026-10-18

- Texterkennung an echten eGrep-Mannschaftsmeldungen verbessert (zwei echte Fotos):
  Foto 1 von 19 auf 33 von 35 Spielern richtig (Nummer + Nachname), Foto 2 von 21 auf 29.
- Tabellenlinien werden vor der Erkennung entfernt (auch schraeg, gestrichelt, grau).
  Sie klebten an den schmalen Spalten Pos. und Nr. ("G | 2" wurde zu "6").
- Grenze zwischen Pos. und Nr. aus den Spaltenkoepfen; "G" wird nicht mehr als Nummer gelesen.
- Name nach Position auf dem Bogen statt nach Textzeile; Namensspalte endet an "Lizenz";
  Namensbeginn ab dem Kopf "Nr." statt festem Abstand.
- Geklammerte Nummern ("(31) BECKER") und Zusaetze nach dem Vornamen ("TK", "GSCMOE")
  gehoeren nicht zum Namen. Trikotnummer aus der Spalte Nr. hat weiter Vorrang.
- "G" in der Spalte Pos. zaehlt schon ab 35 % Erkennungssicherheit (dort stehen nur
  G/LD/RD/C/LF/RF). Start-Markierung bleibt bei 65 % (unsichere Markierung waehlt keinen Starter).

## 1.7 - 2026-10-18

- Fehlerkorrektur Texterkennung: Die Bildgroesse aus der Erkennung wird nicht mehr
  verworfen (Tesseract.js liefert keine Kopfzeile, verworfen wurde die Seitenzeile).
  Vorher konnte die App Spieler am Listenende oder Namensteile rechts verlieren.
  Nachweis: gleiche Eingabe, alter Parser 3 von 6 Spielern, neuer Parser 6 von 6;
  echte Erkennung mit schlichtem Testbild: vorher 1 Spieler je Team, jetzt alle 9.
- Namenspruefung: Komma ist erlaubt (z. B. "Nachname, Vorname").

## 1.6 - 2026-10-18

- Zusammenfassung nach jeder Eingabe: grosse Uhrzeit (wie abgelesen), darunter in
  eGrep-Reihenfolge Team, Ereignis, Nummer (+ Assists), Strafe mit Dauer.
  Das Ereignis ist bereits gespeichert; OK schliesst, Aendern oeffnet die Eingabe,
  Verwerfen loescht es wieder (Rueckgaengig moeglich).
- Spielverlauf: Eintrag antippen oeffnet dieselbe grosse Detailansicht mit Bearbeiten.
  Stift-Symbol entfernt, die ganze Zeile ist antippbar.
- Abgelesene Uhrzeit im Spielverlauf groesser und fett.
- Ereignisauswahl als vier Zeilen untereinander. Farben nach Ereignisart:
  Tor gruen, Strafe orange, Torwartwechsel und Timeout grau.
- OCR: keine Namensliste mehr. Auffaellige Namen werden nur in der Aufstellung gelb
  markiert (mit Grund); Markierung verschwindet nach einmaligem Oeffnen und Speichern.
  Torwart- und Starting-Goalie-Nachfragen bleiben.
- Datenformat 8 (Markierung am Spieler). Daten aus 1.5 werden uebernommen.

## 1.5 - 2026-10-18

- Ereigniseingabe: Uhrzeit -> Was ist passiert? -> Welche Mannschaft? -> Details.
- Neue Ereignisart Timeout (ohne Spielernummer). Zweiter Timeout derselben
  Mannschaft: Nachfrage "nur ein Timeout pro Mannschaft", Speichern nur nach Bestaetigung.
- Eingabefenster mit fester Hoehe in allen Schritten: kein Springen mehr. Ziffernblock
  fuellt den freien Platz (deutlich groessere Tasten), Tasten bleiben bei Torschuetze,
  Assist 1 und Assist 2 exakt an derselben Stelle. "Ohne Assists speichern" unter dem
  Ziffernblock.
- Strafen-Schnellauswahl um "Uebertriebene Haerte" und "Bandencheck" erweitert (8 Knoepfe).
- Spielverlauf: zuletzt eingegebenes Ereignis oben (auch Nachtraege) und vergroessert.
  Bericht, Druck und Text bleiben chronologisch und unveraendert.
- Texterkennung mit deutschem Sprachmodell (Umlaute/ss werden gelesen); APK kleiner.
- Nach der Erkennung: Pruefdialog fuer auffaellige Namen (korrigieren/so lassen/loeschen),
  Nachfrage bei keinem oder nur einem Torwart, Starting-Goalie-Abfrage bei 2+ Torwarten.
- Fehlerkorrektur: Loesch-Bestaetigungen sind jetzt optisch als gefaehrlich markiert.
- Datenformat 7 (neue Ereignisart). Daten aus 1.4 werden unveraendert uebernommen.

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
