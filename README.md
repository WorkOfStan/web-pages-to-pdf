# Web Pages To PDF

Convert your Pocket export or any URL list into organized PDFs for offline backup and archiving.

A simple Python tool to convert your Pocket export or any URL+label list into PDFs, organized by labels for easy offline backup.

## Why?

[Pocket is sunsetting](https://support.mozilla.org/en-US/kb/future-of-pocket) — export your saved articles now and archive them as PDFs, sorted in folders by tags.  
Supports fallback to Wayback Machine if the original page is inaccessible.

## Features

- Parse Pocket CSV export to extract URLs and labels.
- Download web pages as PDFs.
- Organize PDFs in folders named by label. - This script uses only the first tag for folder. (Todo: You can extend to multiple labels.)
- Fallback to Wayback Machine archive if original URL is inaccessible.
- Configurable PDF file naming. - PDF naming uses title + domain + index for uniqueness.
- Tags delimiters are `,` and `|`.
- Tries to download URLs directly, if previous attempts fail. Some pages block indirect attempts. Some pages really don't exist anymore.
- Logs unsuccessful and doubtful downloads into url_retrieval.log.
- Coloured output for better orientation (BLUE = start, RED = wrong, GREEN = correct).

## Requirements

- Python 3.7+
- Chrome (used for headless rendering; wkhtmltopdf could be used instead)

## Installation

1. Clone the repository or download the script.
2. Install Python dependencies:

```bash
   pip install -r requirements.txt
```

## Usage

```bash
python pocket_export_pdf.py --input sample_export.csv --output ./pdf_archive [--chrome "/path/to/chrome."]
```

### Path to Chrome

- Windows: "C:/Program Files/Google/Chrome/Application/chrome.exe"
- macOS: "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
- Linux: usually just "google-chrome" or "chrome"
