# Third-party notices

This project bundles Tesseract.js, tesseract.js-core and the Tesseract German trained-data model (tessdata_fast deu.traineddata) for offline optical character recognition.

- Tesseract.js: Copyright (c) 2015-2025 Tesseract.js contributors.
- Tesseract OCR and trained data: Copyright their respective contributors.
- License: Apache License 2.0. The complete license text is included in `APACHE-2.0.txt`.

Since 2.9 the project also bundles PDF.js (pdfjs-dist 3.11.174, legacy build: `pdf.min.js`, `pdf.worker.min.js`) to read line-ups from PDF files.

- PDF.js: Copyright Mozilla Foundation and PDF.js contributors.
- License: Apache License 2.0 (text in `APACHE-2.0.txt`).
- Documents are opened with `isEvalSupported: false` (mitigation for CVE-2024-4367). Only files chosen by the user are opened; the app has no internet permission.

Club logos (`teamlogos.js`: hockeydata, as used by ehv-nrw.de; `clubs.js`: member list of ehv-nrw.de) are trademarks of the respective clubs and are not covered by the Apache License. The NEV logo is supplied by the user for this application.
