# Third-party notices

This project bundles Tesseract.js, tesseract.js-core and the Tesseract German trained-data model (tessdata_fast deu.traineddata, since 1.5; previously English) for offline optical character recognition.

- Tesseract.js: Copyright (c) 2015-2025 Tesseract.js contributors.
- Tesseract OCR and trained data: Copyright their respective contributors.
- License: Apache License 2.0. The complete license text is included in `APACHE-2.0.txt`.

The NEV logo is supplied by the user for this application and is not covered by the Apache License notice above.

Since 2.9 the project also bundles PDF.js (pdfjs-dist 3.11.174, legacy build: `pdf.min.js`, `pdf.worker.min.js`) to read line-ups from PDF files.

- PDF.js: Copyright Mozilla Foundation and PDF.js contributors.
- License: Apache License 2.0 (text in `APACHE-2.0.txt`).
- Source: npm package pdfjs-dist@3.11.174 (integrity sha512 checked on download).
- Security: documents are opened with `isEvalSupported: false` (mitigation for CVE-2024-4367, as recommended by the PDF.js project for versions before 4.2.67). Only files chosen by the user are opened; the app has no internet permission.

Since 3.0 `clubs.js` contains the member list and club logos of ehv-nrw.de (fetched 20.11.2026, downscaled to 96 px). The logos are trademarks of the respective clubs and are not covered by the Apache License.
