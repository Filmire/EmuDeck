import os
import json
import sys
import re
import subprocess
import hashlib

from vars import home_dir, msg_file
from utils import getSettings

settings = getSettings()
storage_path = os.path.expandvars(settings["storagePath"])

# Function to write messages to the log file
def log_message(message):
    with open(msg_file, "w") as log_file:  # "a" to append messages without overwriting
        log_file.write(message + "\n")

def generate_game_lists(roms_path, images_path):
    def calculate_hash(file_path):
        import hashlib
        hash_md5 = hashlib.md5()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(65536), b""):  # 64 KB chunks
                    hash_md5.update(chunk)
            print(file_path , hash_md5.hexdigest())
            return hash_md5.hexdigest()
        except Exception:
            return None

    def collect_game_data(system_dir, extensions):
        game_data = []
        for root, _, files in os.walk(system_dir):
            for file in files:
                file_path = os.path.join(root, file)
                if os.path.islink(file_path):
                    continue

                filename = os.path.basename(file)
                extension = filename.split('.')[-1]
                name = '.'.join(filename.split('.')[:-1])
                if extension in extensions:

                    platform = os.path.basename(system_dir)

                    # Special cases for WiiU and PS3
                    if os.name != 'nt':
                        if "wiiu" in system_dir:
                            parts = root.split(os.sep)
                            name = parts[-2] if len(parts) >= 2 else name
                            platform = "wiiu"
                        if "ps3" in system_dir:
                            parts = root.split(os.sep)
                            name = parts[-3] if len(parts) >= 3 else name
                            platform = "ps3"
                        if "xbox360" in system_dir:
                            platform = "xbox360"
                    if "ps4" in system_dir:
                        parts = root.split(os.sep)
                        name = parts[-3] if len(parts) >= 3 else name
                        platform = "ps4"

                    # Clean the game name
                    name_cleaned = re.sub(r'\(.*?\)', '', name)
                    name_cleaned = re.sub(r'\[.*?\]', '', name_cleaned)
                    name_cleaned = name_cleaned.strip().replace(' ', '_').replace('-', '_')
                    name_cleaned = re.sub(r'_+', '_', name_cleaned)
                    name_cleaned = name_cleaned.replace('+', '').replace('&', '').replace('!', '').replace("'", '').replace('.', '').replace('_decrypted','').replace('decrypted','').replace('.ps3', '')

                    name_cleaned_pegasus = name.replace(',_', ',')
                    name_cleaned = name_cleaned.lower()

                    # Check for missing images
                    for img_type, ext in [("box2dfront", ".jpg"), ("wheel", ".png"), ("box2dfront", ".jpg")]:
                        img_path = os.path.join(images_path, f"{platform}/media/{img_type}/{name_cleaned}{ext}")
                        if not os.path.exists(img_path):
                            log_message(f"Missing image: {img_path}")

                            game_info = {
                                "name": name_cleaned,
                                "platform": platform,
                                "type": img_type
                            }
                            game_data.append(game_info)

        return sorted(game_data, key=lambda x: x['name'])

    roms_dir = roms_path
    valid_system_dirs = []

    for system_dir in os.listdir(roms_dir):
        if os.name != 'nt':
            if system_dir == "xbox360":
                system_dir = "xbox360/roms"
            if system_dir == "model2":
                system_dir = "model2/roms"
            if system_dir == "ps4":
                system_dir = "ps4/shortcuts"
        full_path = os.path.join(roms_dir, system_dir)
        if os.path.isdir(full_path) and not os.path.islink(full_path) and os.path.isfile(os.path.join(full_path, 'metadata.txt')):
            file_count = sum([len(files) for r, d, files in os.walk(full_path) if not os.path.islink(r)])
            if file_count > 2:
                valid_system_dirs.append(full_path)
                log_message(f"MA: Valid system directory found: {full_path}")

    game_list = []

    for system_dir in valid_system_dirs:
        if any(x in system_dir for x in ["/model2", "/genesiswide", "/mame", "/emulators", "/desktop"]):
            log_message(f"MA: Skipping directory: {system_dir}")
            continue

        with open(os.path.join(system_dir, 'metadata.txt')) as f:
            metadata = f.read()
        collection = next((line.split(':')[1].strip() for line in metadata.splitlines() if line.startswith('collection:')), '')
        shortname = next((line.split(':')[1].strip() for line in metadata.splitlines() if line.startswith('shortname:')), '')
        launcher = next((line.split(':', 1)[1].strip() for line in metadata.splitlines() if line.startswith('launch:')), '').replace('"', '\\"')
        extensions = next((line.split(':')[1].strip().replace(',', ' ') for line in metadata.splitlines() if line.startswith('extensions:')), '').split()

        games = collect_game_data(system_dir, extensions)
        if games:
            system_info = {
                "title": collection,
                "id": shortname,
                "launcher": launcher,
                "games": games
            }
            game_list.append(system_info)
            log_message(f"MA: Detected {len(games)} games from {system_dir}")

    json_output = json.dumps(sorted(game_list, key=lambda x: x['title']), indent=4)

    output_file = os.path.join(storage_path, "retrolibrary/cache/missing_artwork_no_hash.json")

    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, 'w') as f:
        f.write(json_output)
        #print(json_output)

roms_path = sys.argv[1]
images_path = sys.argv[2]

log_message("MA: Missing artwork list generation in progress...")
generate_game_lists(roms_path, images_path)
log_message("MA: Missing artwork list process completed.")