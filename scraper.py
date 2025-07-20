#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SuperPSX PS4 Scraper
Extrae enlaces de descarga de juegos PS4 desde SuperPSX.com

Prioridades de servidores:
1. VikingFile
2. AkiraBox 
3. 1Fichier

Excluye: filecrypt.cc
"""

import json
import requests
from bs4 import BeautifulSoup
import time
import re
import os
from urllib.parse import urljoin, urlparse
import sys

def extract_game_info(soup):
    info = {
        'region': 'USA',
        'size': None,
        'version': '1.00', 
        'release': None,
        'min_fw': None,
        'cover_url': None
    }

    # Buscar tabla con información del juego
    table = soup.find('table')
    if table:
        rows = table.find_all('tr')
        for row in rows:
            cells = row.find_all('td')
            if len(cells) >= 2:
                key = cells[0].get_text().strip()
                value = cells[1].get_text().strip()

                if 'Size' in key:
                    info['size'] = value
                elif 'Version' in key:
                    if 'USA' in value:
                        info['region'] = 'USA'
                    elif 'EUR' in value:
                        info['region'] = 'EUR'
                    elif 'JAP' in value:
                        info['region'] = 'JAP'
                    # Extraer versión CUSA
                    version_match = re.search(r'v?(\d+\.\d+)', value)
                    if version_match:
                        info['version'] = version_match.group(1)
                elif 'Update' in key:
                    update_match = re.search(r'v?(\d+\.\d+)', value)
                    if update_match:
                        info['version'] = update_match.group(1)
                elif 'Required Firmware' in key or 'Firmware' in key:
                    info['min_fw'] = value
                elif 'Release Date' in key:
                    info['release'] = value

    # Buscar cover de imagen
    cover_img = soup.find('img', {'class': ['wp-post-image', 'attachment-post-thumbnail']})
    if cover_img:
        info['cover_url'] = cover_img.get('src')

    return info

def extract_dll_page_links(dll_url, game_name, game_info):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    links = {}

    try:
        response = requests.get(dll_url, headers=headers, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # Buscar enlaces de VikingFile (Prioridad 1)
        viki_links = soup.find_all('a', string=re.compile('Viki', re.IGNORECASE))
        for link in viki_links:
            href = link.get('href')
            if href:
                print(f"  🟢 VikingFile encontrado: {href}")
                # Construir información para este enlace
                link_info = game_info.copy()
                link_info['name'] = game_name

                # Determinar si es game, update o DLC basado en la URL/contexto
                if 'update' in href.lower() or 'patch' in href.lower():
                    link_info['type'] = 'update'
                elif 'dlc' in href.lower():
                    link_info['type'] = 'dlc'
                else:
                    link_info['type'] = 'game'

                links[href] = link_info

        # Buscar enlaces de AkiraBox (Prioridad 2)
        akr_links = soup.find_all('a', string=re.compile('AKR', re.IGNORECASE))
        for link in akr_links:
            href = link.get('href')
            if href and 'akirabox.com' in href:
                print(f"  🟠 AkiraBox encontrado: {href}")
                link_info = game_info.copy()
                link_info['name'] = game_name

                if 'update' in href.lower() or 'patch' in href.lower():
                    link_info['type'] = 'update'
                elif 'dlc' in href.lower():
                    link_info['type'] = 'dlc'
                else:
                    link_info['type'] = 'game'

                links[href] = link_info

        # Buscar enlaces de 1fichier (Prioridad 3)
        onefile_links = soup.find_all('a', string=re.compile('OneFile|1fichier', re.IGNORECASE))
        for link in onefile_links:
            href = link.get('href')
            if href and '1fichier.com' in href:
                print(f"  🟡 1Fichier encontrado: {href}")
                link_info = game_info.copy()
                link_info['name'] = game_name

                if 'update' in href.lower() or 'patch' in href.lower():
                    link_info['type'] = 'update'
                elif 'dlc' in href.lower():
                    link_info['type'] = 'dlc'
                else:
                    link_info['type'] = 'game'

                links[href] = link_info

        if not links:
            print(f"  ❌ No se encontraron enlaces válidos en {dll_url}")

    except Exception as e:
        print(f"  ❌ Error extrayendo enlaces DLL: {e}")

    return links

def extract_download_links(game_url, game_name):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    try:
        print(f"Procesando: {game_name}")
        response = requests.get(game_url, headers=headers, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # Buscar información del juego desde la tabla
        game_info = extract_game_info(soup)

        # Buscar botón de descarga que redirige a página DLL
        download_button = soup.find('a', {'href': re.compile(r'/dll-')})

        if not download_button:
            print(f"  ❌ No se encontró botón de descarga para {game_name}")
            return {}

        dll_url = urljoin(game_url, download_button.get('href'))
        print(f"  🔗 Página DLL encontrada: {dll_url}")

        # Extraer enlaces de la página DLL
        return extract_dll_page_links(dll_url, game_name, game_info)

    except Exception as e:
        print(f"  ❌ Error procesando {game_name}: {e}")
        return {}

def main():
    print("🚀 Iniciando SuperPSX PS4 Scraper")

    # Cargar archivo JSON de juegos
    if not os.path.exists("ps4_games_list.json"):
        print("❌ Error: Archivo ps4_games_list.json no encontrado")
        return

    with open("ps4_games_list.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    print(f"📋 Procesando {len(data['games'])} juegos...")

    # Diccionarios para separar por tipo
    games_output = {}
    updates_output = {}
    dlc_output = {} 

    processed = 0
    errors = 0

    for game in data["games"]:
        name = game["name"]
        url = game["url"]

        try:
            links = extract_download_links(url, name)

            for link_url, info in links.items():
                link_type = info.get('type', 'game')

                if link_type == 'update':
                    updates_output[link_url] = {k: v for k, v in info.items() if k != 'type'}
                elif link_type == 'dlc':
                    dlc_output[link_url] = {k: v for k, v in info.items() if k != 'type'}
                else:
                    games_output[link_url] = {k: v for k, v in info.items() if k != 'type'}

            processed += 1

        except Exception as e:
            print(f"❌ Error procesando {name}: {e}")
            errors += 1

        # Pausa entre requests para evitar rate limiting
        time.sleep(1)

        # Status cada 10 juegos
        if processed % 10 == 0:
            print(f"📊 Progreso: {processed} juegos procesados, {errors} errores")

    # Guardar resultados en archivos separados
    print(f"💾 Guardando resultados...")

    # Formato compatible con FPKGi
    games_data = {"DATA": games_output}
    updates_data = {"DATA": updates_output}
    dlc_data = {"DATA": dlc_output}

    with open("games.json", "w", encoding="utf-8") as f:
        json.dump(games_data, f, indent=2, ensure_ascii=False)

    with open("updates.json", "w", encoding="utf-8") as f:
        json.dump(updates_data, f, indent=2, ensure_ascii=False)

    with open("DLC.json", "w", encoding="utf-8") as f:
        json.dump(dlc_data, f, indent=2, ensure_ascii=False)

    print(f"✅ Scraping completado!")
    print(f"📈 Estadísticas finales:")
    print(f"  - Juegos procesados: {processed}")
    print(f"  - Errores: {errors}")
    print(f"  - Enlaces de juegos: {len(games_output)}")
    print(f"  - Enlaces de updates: {len(updates_output)}")
    print(f"  - Enlaces de DLC: {len(dlc_output)}")

if __name__ == "__main__":
    main()
