"""
PocketExportPDF

This module converts Pocket CSV exports or URL lists into organized PDFs
using Chrome in headless mode. It supports fallback to archive.org if URLs
are not accessible.
"""

import argparse
import csv
import logging
import os
import re
import subprocess
from shutil import which
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

BLUE = "\033[34m"
GREEN = "\033[32m"
RED = "\033[31m"
RESET = "\033[0m"
WAYBACK_API = "http://archive.org/wayback/available?url={url}"

# Configure logger once, near the top of your script
logging.basicConfig(
    filename="url_retrieval.log",  # file to write to
    level=logging.INFO,  # log level
    format="%(asctime)s %(levelname)s: %(message)s",
)


def sanitize_filename(name):
    """Remove invalid filename characters."""
    return re.sub(r'[\\/*?:"<>|]', "", name).strip()


def save_pdf_with_chrome(url: str,
                         output_path: str,
                         chrome_path: str = "chrome",
                         timeout: int = 25) -> bool:
    """
    Save the web page at the given URL as a PDF file using headless Chrome.

    Args:
        url (str): URL of the web page to save.
        output_path (str): Full file path to save the PDF.
        chrome_path (str): Path to Chrome or Chromium executable.
        timeout (int): The Chrome process is aborted if it runs longer than *timeout* seconds.

    Returns:
        bool: True if PDF was created successfully, False on any failure (timeout or non-zero exit).
    """
    # Resolve chrome executable if only a bare name is given
    chrome_exe = which(chrome_path) or chrome_path

    absolute_path = os.path.abspath(output_path)
    # Build the command as a list to avoid shell-quoting problems
    cmd = [
        chrome_exe,
        "--headless",
        "--disable-gpu",
        f"--print-to-pdf={absolute_path}",
        url,
    ]    
    try:
        subprocess.run(cmd, check=True, timeout=timeout)
        print(f"{GREEN}Saved PDF: {absolute_path}{RESET}")
        return True

    except subprocess.TimeoutExpired as e:
        print(f"{RED}Timeout after {e.timeout}s generating PDF for {url}{RESET}")
        return False

    except subprocess.CalledProcessError as e:
        print(f"{RED}Error generating PDF for {url}: {e}{RESET}")
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
        print(f"{RED}Wayback API error for {url}: {e}{RESET}")
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
    Tags delimiters are `,` and `|`.

    Args:
        file_path (str): Path to Pocket CSV export file.

    Returns:
        list of dict: Each dict contains 'url', 'title', 'tags' (list).
    """
    links = []
    with open(file_path, newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            url = row.get("resolved_url") or row.get("given_url") or row.get("url")
            title = (
                row.get("resolved_title")
                or row.get("given_title")
                or row.get("title")
                or "untitled"
            )
            tags_str = row.get("tags") or ""
            tags = (
                [t.strip() for t in tags_str.replace("|", ",").split(",")]
                if tags_str
                else []
            )
            if url:
                links.append({"url": url, "title": title, "tags": tags})
    # debug
    # print("links")
    # print(links)
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
        print(f"{BLUE}Processing ({idx}/{len(links)}): {url}{RESET}")
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
            print(f"{RED}URL not accessible: {url}{RESET}")

        if not success:
            print(f"Trying Wayback Machine fallback for {url}")
            archive_url = fetch_wayback_url(url)
            if archive_url:
                print(f"{GREEN}Found archive.org snapshot: {archive_url}{RESET}")
                success2 = save_pdf_with_chrome(
                    archive_url, output_path, chrome_path=chrome_path
                )
                if not success2:
                    logging.warning(
                        "Failed downloading archive.org snapshot: %s", archive_url
                    )
            else:
                print(f"{RED}No archive.org snapshot found for {url}{RESET}")
                print(
                    "Trying directly one more time."
                )  # e.g. for 404 response (could be made optional)
                success2 = save_pdf_with_chrome(
                    url, output_path, chrome_path=chrome_path
                )
                if success2:
                    logging.warning(
                        'Double check downloading snapshot directly: %s : "%s"',
                        url,
                        output_path,
                    )
                else:
                    logging.warning("Failed downloading snapshot directly: %s", url)


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
