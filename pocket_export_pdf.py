import os
import re
import argparse
import pdfkit
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse

WAYBACK_API = "http://archive.org/wayback/available?url={url}"

def sanitize_filename(name):
    # Remove invalid filename characters
    return re.sub(r'[\\/*?:"<>|]', "", name).strip()

def fetch_wayback_url(url):
    """Check archive.org for closest snapshot URL."""
    try:
        r = requests.get(WAYBACK_API.format(url=url), timeout=10)
        r.raise_for_status()
        data = r.json()
        snapshots = data.get('archived_snapshots', {})
        if 'closest' in snapshots:
            return snapshots['closest']['url']
    except Exception as e:
        print(f"Wayback API error for {url}: {e}")
    return None

def download_pdf(url, output_path):
    """Download URL as PDF with pdfkit."""
    options = {
        'quiet': '',
        'enable-local-file-access': '',
        'no-outline': None,
        'print-media-type': None
    }
    try:
        pdfkit.from_url(url, output_path, options=options)
        print(f"Saved PDF: {output_path}")
        return True
    except Exception as e:
        print(f"Failed to save PDF for {url}: {e}")
        return False

def parse_pocket_export(file_path):
    """Parse Pocket export HTML and return list of dict {url, title, tags}."""
    with open(file_path, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f, 'html.parser')
    links = []
    for a in soup.find_all('a', href=True):
        url = a['href']
        title = a.get_text(strip=True) or "untitled"
        tags = a.get('data-tag')
        if tags:
            tags = [t.strip() for t in tags.split(',')]
        else:
            tags = []
        links.append({'url': url, 'title': title, 'tags': tags})
    return links

def save_pdfs(links, base_dir):
    """Download PDFs for all links, organized by tags."""
    os.makedirs(base_dir, exist_ok=True)
    for idx, link in enumerate(links, 1):
        url = link['url']
        title = sanitize_filename(link['title']) or f"page_{idx}"
        tags = link['tags'] or ['Unlabeled']

        folder = os.path.join(base_dir, sanitize_filename(tags[0]))
        os.makedirs(folder, exist_ok=True)

        domain = urlparse(url).netloc.replace("www.", "")
        filename = f"{title}_{domain}_{idx}.pdf"
        filepath = os.path.join(folder, filename)

        if download_pdf(url, filepath):
            continue

        print(f"Trying Wayback Machine fallback for {url}")
        archive_url = fetch_wayback_url(url)
        if archive_url:
            download_pdf(archive_url, filepath)
        else:
            print(f"Could not archive or download {url}")

def main():
    parser = argparse.ArgumentParser(description="Convert Pocket export or URL list to PDFs")
    parser.add_argument('--input', required=True, help='Path to Pocket export HTML file')
    parser.add_argument('--output', required=True, help='Output directory for PDFs')
    args = parser.parse_args()

    print(f"Parsing export file: {args.input}")
    links = parse_pocket_export(args.input)
    print(f"Found {len(links)} links.")

    save_pdfs(links, args.output)

if __name__ == "__main__":
    main()
