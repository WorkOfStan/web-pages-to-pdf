import argparse
import csv
import os
import re
import subprocess
import shlex
from urllib.parse import urlparse

from bs4 import BeautifulSoup

WAYBACK_API = "http://archive.org/wayback/available?url={url}"


def sanitize_filename(name):
    """Remove invalid filename characters."""
    return re.sub(r'[\\/*?:"<>|]', "", name).strip()


def save_pdf_with_chrome(url, output_path, chrome_path='chrome'):
    absolute_path = os.path.abspath(output_path)
    cmd = f'"{chrome_path}" --headless --disable-gpu --no-margins --print-to-pdf="{absolute_path}" "{url}"'
    try:
        subprocess.run(shlex.split(cmd), check=True)
        print(f"Saved PDF: {absolute_path}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error generating PDF for {url}: {e}")
        return False


def fetch_wayback_url(url):
    """Check archive.org for closest snapshot URL."""
    try:
        r = requests.get(WAYBACK_API.format(url=url), timeout=10)
        r.raise_for_status()
        data = r.json()
        snapshots = data.get("archived_snapshots", {})
        if "closest" in snapshots:
            return snapshots["closest"]["url"]
    except Exception as e:
        print(f"Wayback API error for {url}: {e}")
    return None


def html_parse_pocket_export(file_path):
    """Parse Pocket export HTML and return list of dict {url, title, tags}."""
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
    Parse Pocket CSV export and return list of dict {url, title, tags}.
    """
    links = []
    with open(file_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            url = row.get('resolved_url') or row.get('given_url')  # fallback if resolved_url missing
            title = row.get('resolved_title') or row.get('given_title') or "untitled"
            tags_str = row.get('tags') or ""
            tags = [t.strip() for t in tags_str.split(',')] if tags_str else []
            if url:
                links.append({'url': url, 'title': title, 'tags': tags})
    return links


def generate_pdfs(links, output_dir, chrome_path):
    os.makedirs(output_dir, exist_ok=True)

    for idx, link in enumerate(links, 1):
        url = link['url']
        title = sanitize_filename(link['title']) or f"page_{idx}"
        tags = link['tags'] or ['Unlabeled']

        folder = os.path.join(output_dir, sanitize_filename(tags[0]))
        os.makedirs(folder, exist_ok=True)

        domain = urlparse(url).netloc.replace("www.", "")
        filename = f"{title}_{domain}_{idx}.pdf"
        output_path = os.path.join(folder, filename)

        print(f"Processing ({idx}/{len(links)}): {url}")
        if save_pdf_with_chrome(url, output_path, chrome_path=chrome_path):
            continue

        print(f"Failed to download live page, trying Wayback Machine fallback for {url}")
        archive_url = fetch_wayback_url(url)
        if archive_url:
            print(f"Found archive.org snapshot: {archive_url}")
            if not save_pdf_with_chrome(archive_url, output_path, chrome_path=chrome_path):
                print(f"Failed to save PDF from archive.org for {url}")
        else:
            print(f"No archive.org snapshot found for {url}")


def main():
    parser = argparse.ArgumentParser(description="Convert Pocket export or URL list to PDFs via Chrome headless")
    parser.add_argument('--input', required=True, help='Path to Pocket export HTML file')
    parser.add_argument('--output', required=True, help='Output directory for PDFs')
    parser.add_argument('--chrome', default='chrome', help='Path to Chrome/Chromium executable (default: "chrome")')
    args = parser.parse_args()

    print(f"Parsing export file: {args.input}")
    links = parse_pocket_export(args.input)
    print(f"Found {len(links)} links.")

    generate_pdfs(links, args.output, args.chrome)


if __name__ == "__main__":
    main()
