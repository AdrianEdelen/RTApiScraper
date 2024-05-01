import os
import requests
import json
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm
import argparse

def download_image(url, path):
    if not os.path.exists(path):  # Only download if file does not exist
        response = requests.get(url)
        if response.status_code == 200:
            with open(path, 'wb') as f:
                f.write(response.content)
            return "Downloaded"
        return "Failed to download"
    return "Already exists"

def get_path_structure(url, base_dir, human_readable, slug, size, dry_run=False):
    
    if 'dev.cdn' in url:
        a = True
    #normalized_url = url.replace("dev.cdn.roosterteeth.com", "cdn.roosterteeth.com")
    normalized_url = url.replace("s3.amazonaws.com/dev.cdn.roosterteeth.com", "cdn.roosterteeth.com")

    if human_readable:
        full_path = os.path.join(base_dir, slug)
        filename = f"{slug}_{size}.png"
    else:
        path_parts = normalized_url.split("/")[3:-1]
        file_name = normalized_url.split("/")[-1]
        full_path = os.path.join(base_dir, *path_parts)
        filename = file_name

    if not dry_run:
        os.makedirs(full_path, exist_ok=True)

    return os.path.join(full_path, filename)



def load_json_files(json_paths):
    combined_data = {'data': []}
    for path in json_paths:
        with open(path, 'r') as file:
            data = json.load(file)
            combined_data['data'].extend(data['data'])
    return combined_data

def main(args):
    json_data = load_json_files(args.json_files)

    seen_urls = set() 
    downloads = []

    for entry in json_data['data']:
        attributes = entry['attributes']
        slug = attributes.get('slug', 'default_slug')
        images = entry.get('included', {}).get('images', [])
        for image in images:
            for size in ['large', 'medium', 'small', 'thumb']:
                image_url = image['attributes'].get(size)
                if image_url and image_url not in seen_urls:
                    seen_urls.add(image_url)
                    file_path = get_path_structure(image_url, args.base_dir, args.human_readable, slug, size)
                    downloads.append((image_url, file_path))

    if args.dry_run:
        print(f"Total unique links found: {len(seen_urls)}")
    else:
        with ThreadPoolExecutor(max_workers=10) as executor:
            results = list(tqdm(executor.map(lambda x: download_image(*x), downloads), total=len(downloads), desc="Downloading images"))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download images based on JSON configuration.")
    parser.add_argument('--json_files', nargs='+', required=True, help='Paths to the JSON files containing the data.')
    parser.add_argument('--human_readable', action='store_true', help='Toggle human readable paths.')
    parser.add_argument('--base_dir', default='downloaded_images', help='Base directory for storing downloaded images.')
    parser.add_argument('--dry_run', action='store_true', help='Run without making directories or downloading files.')
    args = parser.parse_args()
    main(args)
