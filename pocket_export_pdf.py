"""
PocketExportPDF

This module converts Pocket CSV exports or URL lists into organized PDFs
using Chrome in headless mode. It supports fallback to archive.org if URLs
are not accessible.
"""

import argparse
import csv
import os
import re
import shlex
import subprocess
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

WAYBACK_API = "http://archive.org/wayback/available?url={url}"


def sanitize_filename(name):
    """Remove invalid filename characters."""
    return re.sub(r'[\\/*?:"<>|]', "", name).strip()


def save_pdf_with_chrome(url, output_path, chrome_path="chrome"):
    """
    Save the web page at the given URL as a PDF file using headless Chrome.

    Args:
        url (str): URL of the web page to save.
        output_path (str): Full file path to save the PDF.
        chrome_path (str): Path to Chrome or Chromium executable.

    Returns:
        bool: True if PDF was created successfully, False otherwise.
    """
    absolute_path = os.path.abspath(output_path)
    cmd = f'"{chrome_path}" --headless --disable-gpu --print-to-pdf="{absolute_path}" "{url}"'
    try:
        subprocess.run(shlex.split(cmd), check=True)
        print(f"Saved PDF: {absolute_path}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error generating PDF for {url}: {e}")
        return False


def fetch_wayback_url(url):
    """
    Query archive.org Wayback Machine API for closest archived snapshot URL.

    Args:
        url (str): Original URL to check archive for.

    Returns:
        str or None: Archive URL if available, else None.
    """
    try:
        r = requests.get(WAYBACK_API.format(url=url), timeout=10)
        r.raise_for_status()
        data = r.json()
        snapshots = data.get("archived_snapshots", {})
        if "closest" in snapshots:
            return snapshots["closest"]["url"]
    except requests.RequestException as e:
        print(f"Wayback API error for {url}: {e}")
    return None


def html_parse_pocket_export(file_path):
    """
    Parse Pocket export HTML and return list of dicts with keys: url, title, tags.

    Args:
        file_path (str): Path to Pocket HTML export file.

    Returns:
        list of dict: Each dict contains 'url', 'title', 'tags' (list).
    """
    with open(file_path, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, "html.parser")
    links = []
    for a in soup.find_all("a", href=True):
        url = a["href"]
        title = a.get_text(strip=True) or "untitled"
        tags = a.get("data-tag")
        if tags:
            tags = [t.strip() for t in tags.split(",")]
        else:
            tags = []
        links.append({"url": url, "title": title, "tags": tags})
    return links


def parse_pocket_export(file_path):
    """
    Parse Pocket CSV export and return list of dicts with keys: url, title, tags.

    Args:
        file_path (str): Path to Pocket CSV export file.

    Returns:
        list of dict: Each dict contains 'url', 'title', 'tags' (list).
    """
    links = []
    with open(file_path, newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            url = row.get("resolved_url") or row.get(
                "given_url"
            )  # fallback if resolved_url missing
            title = row.get("resolved_title") or row.get("given_title") or "untitled"
            tags_str = row.get("tags") or ""
            tags = [t.strip() for t in tags_str.split(",")] if tags_str else []
            if url:
                links.append({"url": url, "title": title, "tags": tags})
    return links


def is_url_accessible(url, timeout=5):
    """
    Check if a URL is accessible by sending a GET request.

    Args:
        url (str): URL to check.
        timeout (int): Timeout in seconds for the request.

    Returns:
        bool: True if status code is 200–399, False otherwise.
    """
    try:
        # Some webservers don't answer right to requests.head
        # response = requests.head(url, allow_redirects=True, timeout=timeout)
        response = requests.get(url, stream=True, timeout=timeout)
        print(f"Get response status code: {response.status_code}")
        # Consider accessible if status code is 200–399
        return 200 <= response.status_code < 400
    except requests.RequestException:
        return False


def generate_pdfs(links, output_dir, chrome_path):
    """
    Generate PDFs from list of links organized by tags using Chrome headless.

    Args:
        links (list): List of dicts with 'url', 'title', 'tags'.
        output_dir (str): Base directory to save PDFs.
        chrome_path (str): Path to Chrome executable.
    """
    os.makedirs(output_dir, exist_ok=True)

    for idx, link in enumerate(links, 1):
        url = link["url"]
        print(f"Processing ({idx}/{len(links)}): {url}")
        title = sanitize_filename(link["title"]) or f"page_{idx}"
        tags = link["tags"] or ["Unlabeled"]

        folder = os.path.join(output_dir, sanitize_filename(tags[0]))
        os.makedirs(folder, exist_ok=True)

        domain = urlparse(url).netloc.replace("www.", "")
        filename = f"{title}_{domain}_{idx}.pdf"
        output_path = os.path.join(folder, filename)
        if os.path.exists(output_path):
            print(f"Skipping existing PDF: {output_path}")
            continue

        if is_url_accessible(url, 10):
            success = save_pdf_with_chrome(url, output_path, chrome_path=chrome_path)
        else:
            success = False
            print(f"URL not accessible: {url}")

        if not success:
            print(f"Trying Wayback Machine fallback for {url}")
            archive_url = fetch_wayback_url(url)
            if archive_url:
                print(f"Found archive.org snapshot: {archive_url}")
                save_pdf_with_chrome(archive_url, output_path, chrome_path=chrome_path)
            else:
                print(f"No archive.org snapshot found for {url}")
                # print(f"Trying directly one more time.") # e.g. for 404 response
                # save_pdf_with_chrome(url, output_path, chrome_path=chrome_path)


def main():
    """Main CLI entry point to parse arguments and start PDF generation."""
    parser = argparse.ArgumentParser(
        description="Convert Pocket export or URL list to PDFs via Chrome headless"
    )
    parser.add_argument(
        "--input", required=True, help="Path to Pocket export HTML file"
    )
    parser.add_argument("--output", required=True, help="Output directory for PDFs")
    parser.add_argument(
        "--chrome",
        default="chrome",
        help='Path to Chrome/Chromium executable (default: "chrome")',
    )
    args = parser.parse_args()

    print(f"Parsing export file: {args.input}")
    links = parse_pocket_export(args.input)
    print(f"Found {len(links)} links.")

    generate_pdfs(links, args.output, args.chrome)


if __name__ == "__main__":
    main()
