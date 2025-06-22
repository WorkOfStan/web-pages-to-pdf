# Web Pages To PDF

Convert your Pocket export or any URL list into organized PDFs for offline backup and archiving.

A simple Python tool to convert your Pocket export or any URL+label list into PDFs, organized by labels for easy offline backup.

[Pocket is sunsetting](https://support.mozilla.org/en-US/kb/future-of-pocket) — export your saved articles now and archive them as PDFs, sorted in folders by tags.  
Supports fallback to Wayback Machine if the original page is inaccessible.

## Why?

[Pocket is sunsetting](https://support.mozilla.org/en-US/kb/future-of-pocket), so export your links while you can! This tool converts your Pocket export or any URL+label list into PDFs stored in folders by labels.

## Features

- Parse Pocket HTML export to extract URLs and labels.
- Download web pages as PDFs.
- Organize PDFs in folders named by label.
- Fallback to Wayback Machine archive if original URL is inaccessible.
- Configurable PDF file naming.

## Requirements

- Python 3.7+
- `wkhtmltopdf` binary installed and in your PATH (<https://wkhtmltopdf.org/>)

## Installation

1. Clone the repository or download the script.
2. Create a Python virtual environment (recommended):

```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install Python dependencies:

```bash
   pip install -r requirements.txt
```

4. Make sure `wkhtmltopdf` is installed and accessible from the command line.

## Usage

```bash
python pocket_export_pdf.py --input pocket_export.html --output ./pdf_archive
```
