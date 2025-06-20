# Web Pages To PDF

Convert your Pocket export or any URL list into organized PDFs for offline backup and archiving.

A simple Python tool to convert your Pocket export or any URL+label list into PDFs, organized by labels for easy offline backup.

Pocket is sunsetting — export your saved articles now and archive them as PDFs, sorted in folders by tags.  
Supports fallback to Wayback Machine if the original page is inaccessible.

A tool to export and archive your Pocket saved URLs as PDFs organized by labels.

## Why?

Pocket is sunsetting, so export your links while you can! This tool converts your Pocket export or any URL+label list into PDFs stored in folders by labels.

## Features

- Parse Pocket HTML export to extract URLs and labels.
- Download web pages as PDFs.
- Organize PDFs in folders named by label.
- Fallback to Wayback Machine archive if original URL is inaccessible.
- Configurable PDF file naming.

## Requirements

- Python 3.7+
- `pdfkit` Python package (`pip install pdfkit`)
- `wkhtmltopdf` binary installed and in your PATH (https://wkhtmltopdf.org/)

## Usage

```bash
python pocket_export_pdf.py --input pocket_export.html --output ./pdf_archive
```
