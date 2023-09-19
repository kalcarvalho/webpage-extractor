import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from tqdm import tqdm

# Global set to store processed links
processed_links = set()


def read_domain_from_file():
    with open("domain.txt", "r") as file:
        return file.readline().strip()


def download_page(url):
    # print(f"\nDownload page {url}")
    response = requests.get(url)
    if response.status_code == 200:
        return response.content
    else:
        print(f"Failed to download page from {url}")
        return None


def extract_content(html_content):
    soup = BeautifulSoup(html_content, "html.parser")
    return soup.prettify()


def save_content_to_file(content, filepath):
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)


def create_html_files(url, output_dir, path_dir=None):
    # Create the output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Save the selected links to links.txt
    links_file_path = os.path.join(output_dir, "links.txt")
    with open(links_file_path, "a") as links_file:
        links_file.write(url + "\n")

    # Download the page
    page_content = download_page(url)
    if page_content:
        # Generate the filename based on the URL
        parsed_url = urlparse(url)
        path_parts = [part for part in parsed_url.path.split("/") if part]
        filename = path_parts[-1] if path_parts else "index.html"

        # Save the page as index.html if it's the home page
        if path_dir == None:
            path_dir = output_dir

        if not os.path.exists(path_dir):
            os.makedirs(path_dir)

        page_filename = os.path.join(path_dir, filename)

        # print(f"\nPage Filename: {page_filename}")
        save_content_to_file(extract_content(page_content), page_filename)

        # Extract links and resources and recursively process subpages
        soup = BeautifulSoup(page_content, "html.parser")
        links = soup.find_all("a", href=True)

        for i, link in enumerate(tqdm(links, unit="link"), start=1):
            subpage_url = link["href"]

            # Skip anchor links within the same page
            if subpage_url.startswith("#") or subpage_url.endswith("/"):
                continue

            subpage_url = urljoin(domain, subpage_url)  # Make sure the URL is absolute

            # print(f"\nsubpage: {subpage_url}")

            parsed_subpage_url = urlparse(subpage_url)
            subpage_path_parts = [
                part for part in parsed_subpage_url.path.split("/") if part
            ]
            filename = subpage_path_parts[-1] if subpage_path_parts else "index.html"
            path = os.path.join(output_dir, *subpage_path_parts[:-1])

            # print(f"\nPath: {path}")
            # print(f"\nFile: {filename}")

            # Process subpages recursively
            processed_links.add(subpage_url)
            create_html_files(subpage_url, output_dir, path)

        # Download resources (images, stylesheets, scripts, etc.)
        resources = soup.find_all(["img", "link", "script"], src=True)
        for resource in tqdm(resources, desc="Downloading Resources", unit="resource"):
            resource_url = resource.get("src") or resource.get(
                "href"
            )  # Check 'src' or 'href'
            resource_url = urljoin(url, resource_url)  # Make sure the URL is absolute
            download_resource(resource_url, output_dir)


def download_resource(url, output_dir):
    response = requests.get(url)
    if response.status_code == 200:
        filename = os.path.basename(urlparse(url).path)
        filepath = os.path.join(output_dir, filename)
        with open(filepath, "wb") as f:
            f.write(response.content)


if __name__ == "__main__":
    domain = read_domain_from_file()
    url = f"https://{domain}"
    base_output_dir = os.path.join("output", domain)

    create_html_files(url, base_output_dir)
    print("HTML files and resources saved successfully.")
