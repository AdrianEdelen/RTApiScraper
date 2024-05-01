import os
import requests
import json
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm
import argparse

def check_file_exists(path):
    return os.path.exists(path)

def download_image(url, path):
    if not os.path.exists(path):  # Avoid re-downloading existing files
        response = requests.get(url)
        if response.status_code == 200:
            with open(path, 'wb') as f:
                f.write(response.content)
            return "Downloaded"
        else:
            return "Failed to download"
    return "Already exists"

def get_path_structure(url, base_dir, human_readable, slug, size):
    if human_readable:
        full_path = os.path.join(base_dir, slug)
        filename = f"{slug}_{size}.png"
    else:
        path_parts = url.split("/")[3:-1]
        file_name = url.split("/")[-1]
        full_path = os.path.join(base_dir, *path_parts)
        filename = file_name
    os.makedirs(full_path, exist_ok=True)
    return os.path.join(full_path, filename)

def main(args):
    with open(args.json, 'r') as file:
        json_data = json.load(file)

    file_paths = []
    for entry in json_data['data']:
        attributes = entry['attributes']
        slug = attributes.get('slug', 'default_slug')
        images = entry.get('included', {}).get('images', [])
        for image in images:
            for size in ['large', 'medium', 'small', 'thumb']:
                if image_url := image['attributes'].get(size):
                    file_path = get_path_structure(image_url, args.base_dir, args.human_readable, slug, size)
                    file_paths.append((image_url, file_path))

    downloads_needed = [(url, path) for url, path in file_paths if not check_file_exists(path)]

    with ThreadPoolExecutor(max_workers=10) as executor:
        results = list(tqdm(executor.map(lambda x: download_image(*x), downloads_needed), total=len(downloads_needed), desc="Downloading images"))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download images based on JSON configuration.")
    parser.add_argument('--json', required=True, help='Path to the JSON file containing the data.')
    parser.add_argument('--human_readable', action='store_true', help='Toggle human readable paths.')
    parser.add_argument('--base_dir', default='downloaded_images', help='Base directory for storing downloaded images.')
    args = parser.parse_args()
    main(args)
