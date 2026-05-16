Bundestag OpenData Explorer
A self-contained local web application for browsing, searching, and exporting documents from the German Bundestag via the official DIP API (Dokumentations- und Informationssystem für Parlamentsmaterialien).

Features
🔍 Search

Browse and search across four document types: Plenary Records (Plenarprotokolle), Parliamentary Papers (Drucksachen), Proceedings (Vorgänge), and Members of Parliament
True full-text search using the drucksache-text and plenarprotokoll-text API endpoints — the server scans the full OCR text of each document and streams matching results back in real time, including a context snippet around the keyword
All queries automatically filtered to Bundestag only (f.zuordnung=BT), excluding Bundesrat documents
Cursor-based pagination for navigating large result sets

📑 Index

Browse documents by legislative term (1st–21st Bundestag, 1949–present)
Dedicated A–Z directory for Members of Parliament
Live document counts per dataset
Click any index entry to jump directly to a filtered search

📤 Export

TXT export — downloads a structured .txt file containing metadata and abstracts for all matching documents, formatted for direct import as a source in Google NotebookLM
PDF bulk download — downloads up to 200 original PDFs from the Bundestag document server (dserver.bundestag.de), with automatic URL construction from document numbers and real-time progress logging. Files are saved to bundestag_export/pdf/ for manual import into NotebookLM or any PDF reader


Architecture
The application is a single Python file (~1,300 lines) with no external dependencies beyond the Python standard library. It runs a local HTTP server that:

Serves the entire UI as a dynamically generated HTML page
Proxies all DIP API calls server-side (bypassing browser CORS restrictions)
Handles full-text search by paginating the -text endpoints and filtering results in Python
Streams export progress to the browser via NDJSON (newline-delimited JSON)

Browser  ←→  localhost:8765  ←→  search.dip.bundestag.de/api/v1
                               ←→  dserver.bundestag.de  (PDFs)

Requirements

Python 3.8 or later
No third-party packages required


Usage
bashpython3 avvia_bundestag.py
The browser opens automatically at http://localhost:8765. Press Ctrl+C to stop the server.
Exported files are saved in a bundestag_export/ folder next to the script:

bundestag_export/*.txt — TXT exports
bundestag_export/pdf/*.pdf — downloaded PDFs


API
This application uses the DIP public API provided by the Deutscher Bundestag:

Base URL: https://search.dip.bundestag.de/api/v1
Authentication: public API key (included)
Documentation: dip.bundestag.api.bund.dev
Terms of use: dip.bundestag.de/über-dip/nutzungsbedingungen


Note on full-text search: The DIP API does not expose a server-side full-text search parameter. This application implements full-text search by fetching document pages from the -text endpoints (which include OCR text) and filtering results server-side. Searches over large date ranges may take several seconds.


License
This project is not affiliated with the Deutscher Bundestag. All parliamentary data is © Deutscher Bundestag and subject to their terms of use.
