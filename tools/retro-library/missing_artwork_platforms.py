import os
import json
import sys
import re
import subprocess

from vars import home_dir, msg_file
from utils import getSettings

settings = getSettings()
storage_path = os.path.expandvars(settings["storagePath"])

# Función para escribir en el archivo de log
def log_message(message):
    with open(msg_file, "w") as log_file:  # "a" para agregar mensajes sin sobrescribir
        log_file.write(message + "\n")

def generate_systems_with_missing_images(roms_path, images_path):
    def has_missing_images(system_dir, extensions):
        platform = os.path.basename(system_dir)  # Extrae el nombre de la plataforma del directorio
        media_folder_path = os.path.join(images_path, platform, "media")  # Ruta de la carpeta 'media'

        file_count = sum(
            1 for root, _, files in os.walk(system_dir)
            for file in files
            if not os.path.islink(os.path.join(root, file))
        )

        if file_count <= 3:
            return False

        if not os.path.isdir(media_folder_path):
            return True

        return False

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
                log_message(f"MAP: Valid system directory added: {full_path}")

    systems_with_missing_images = set()

    for system_dir in valid_system_dirs:
        if any(x in system_dir for x in ["/model2", "/genesiswide", "/mame", "/emulators", "/desktop"]):
            log_message(f"MAP: Skipping directory: {system_dir}")
            continue

        with open(os.path.join(system_dir, 'metadata.txt')) as f:
            metadata = f.read()
        extensions = next((line.split(':')[1].strip().replace(',', ' ') for line in metadata.splitlines() if line.startswith('extensions:')), '').split()

        if has_missing_images(system_dir, extensions):
            systems_with_missing_images.add(os.path.basename(system_dir))
            log_message(f"MAP: System with missing images: {os.path.basename(system_dir)}")

    json_output = json.dumps(list(systems_with_missing_images), indent=4)

    output_file = os.path.join(storage_path, "retrolibrary/cache/missing_systems.json")
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, 'w') as f:
        f.write(json_output)

# Pasar la ruta de las ROMs y de las imágenes desde los argumentos de línea de comandos
roms_path = sys.argv[1]
images_path = sys.argv[2]

log_message("MAP: Searching missing artwork in bundles...")
generate_systems_with_missing_images(roms_path, images_path)
log_message("MAP: Completed missing artwork in bundles")
