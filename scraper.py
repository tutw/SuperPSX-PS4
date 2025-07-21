#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SuperPSX PS4 Scraper - Versión Final Optimizada
Extrae enlaces de descarga de juegos PS4 desde SuperPSX.com

Características:
- Prioridad a VikingFile (archivo principal: games.json)
- Archivos separados por servidor (akirabox.json, 1fichier.json, etc.)
- Clasificación automática de games, updates y DLCs
- Obtiene lista de juegos desde GitHub
- Excluye enlaces de filecrypt.cc

Uso:
- python scraper.py                    (modo prueba, 50 juegos)
- python scraper.py --full             (modo completo, todos los juegos)
- python scraper.py --games 100        (modo personalizado, 100 juegos)
"""

import json
import requests
from bs4 import BeautifulSoup
import time
import re
import os
import argparse
from urllib.parse import urljoin, urlparse
import sys

def extract_game_info(soup):
    """Extrae información básica del juego desde la página principal"""
    info = {
        'region': 'EUR',  # Default a EUR
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

                if 'Size' in key or 'Tamaño' in key:
                    info['size'] = value
                elif 'Version' in key or 'Versión' in key:
                    if 'USA' in value:
                        info['region'] = 'USA'
                    elif 'EUR' in value:
                        info['region'] = 'EUR'
                    elif 'JAP' in value or 'JPN' in value:
                        info['region'] = 'JAP'
                    # Extraer código CUSA si existe
                    cusa_match = re.search(r'CUSA\d+', value)
                    if cusa_match:
                        info['cusa'] = cusa_match.group(0)
                elif 'Required Firmware' in key or 'Firmware' in key:
                    info['min_fw'] = value
                elif 'Release Date' in key or 'Fecha' in key:
                    info['release'] = value

    # Buscar cover de imagen
    cover_img = soup.find('img', {'class': ['wp-post-image', 'attachment-post-thumbnail']})
    if not cover_img:
        cover_img = soup.find('img', {'src': lambda x: x and any(ext in x for ext in ['.jpg', '.png', '.webp']) and 'cover' in x.lower()})

    if cover_img:
        info['cover_url'] = cover_img.get('src')

    return info

def classify_link_type(key_text):
    """Clasifica el tipo de enlace basándose en el texto de la primera columna"""
    key_lower = key_text.lower()

    # Identificar updates
    if any(word in key_lower for word in ['update', 'patch', 'actualización', 'parche']):
        return 'update'

    # Identificar DLCs
    if any(word in key_lower for word in ['dlc', 'dlcs', 'expansion', 'add-on', 'addon']):
        return 'dlc'

    # Por defecto, es un juego base
    if any(word in key_lower for word in ['game', 'juego', 'base']):
        return 'game'

    # Si no tiene identificador claro, asumir que es juego base
    return 'game'

def get_server_name(url):
    """Obtiene el nombre del servidor basándose en la URL"""
    if 'vikingfile.com' in url:
        return 'vikingfile'
    elif 'akirabox.com' in url:
        return 'akirabox'
    elif '1fichier.com' in url:
        return '1fichier'
    elif 'mega' in url.lower():
        return 'mega'
    elif 'mediafire' in url.lower():
        return 'mediafire'
    else:
        domain = urlparse(url).netloc
        return domain.replace('www.', '').replace('.com', '').replace('.net', '').replace('.org', '')

def extract_dll_page_links(dll_url, game_name, game_info, verbose=True):
    """Extrae todos los enlaces de la página DLL y los clasifica"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    server_links = {
        'vikingfile': {},
        'akirabox': {},
        '1fichier': {},
        'other': {}
    }

    try:
        response = requests.get(dll_url, headers=headers, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # Buscar tabla principal con enlaces
        tables = soup.find_all('table')
        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all('td')
                if len(cells) >= 2:
                    key = cells[0].get_text().strip()

                    # Clasificar el tipo de contenido
                    content_type = classify_link_type(key)

                    # Buscar todos los enlaces en la segunda celda
                    links = cells[1].find_all('a')
                    for link in links:
                        href = link.get('href')
                        text = link.get_text().strip()

                        if not href or 'filecrypt.cc' in href:
                            continue  # Excluir filecrypt

                        # Crear información del enlace
                        link_info = game_info.copy()
                        link_info['name'] = game_name
                        link_info['type'] = content_type
                        link_info['download_text'] = text
                        link_info['key_description'] = key

                        # Extraer información adicional del key (firmware, versión, etc.)
                        if '(' in key and ')' in key:
                            parenthesis_content = re.findall(r'\((.*?)\)', key)
                            for content in parenthesis_content:
                                if any(fw in content for fw in ['5.05', '6.72', '7.02', '7.55', '9.00', '11.00', '12.00']):
                                    link_info['min_fw'] = content
                                elif 'v' in content and any(c.isdigit() for c in content):
                                    link_info['version'] = content.replace('v', '').strip()

                        # Clasificar por servidor
                        server = get_server_name(href)

                        if server == 'vikingfile':
                            server_links['vikingfile'][href] = link_info
                            if verbose:
                                print(f"  🏆 VIKINGFILE ({content_type}): {key} => {text}")
                        elif server == 'akirabox':
                            server_links['akirabox'][href] = link_info
                            if verbose:
                                print(f"  ⚡ AKIRABOX ({content_type}): {key} => {text}")
                        elif server == '1fichier':
                            server_links['1fichier'][href] = link_info
                            if verbose:
                                print(f"  📁 1FICHIER ({content_type}): {key} => {text}")
                        else:
                            server_links['other'][href] = link_info
                            if verbose:
                                print(f"  🌐 {server.upper()} ({content_type}): {key} => {text}")

        # Estadísticas de lo encontrado
        total_links = sum(len(server_links[server]) for server in server_links)
        if total_links == 0:
            if verbose:
                print(f"  ❌ No se encontraron enlaces válidos en {dll_url}")
        else:
            if verbose:
                print(f"  ✅ Encontrados {total_links} enlaces válidos")

    except Exception as e:
        if verbose:
            print(f"  ❌ Error extrayendo enlaces DLL: {e}")

    return server_links

def extract_download_links(game_url, game_name, verbose=True):
    """Extrae enlaces de descarga de un juego específico"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    try:
        if verbose:
            print(f"🎮 Procesando: {game_name}")
        response = requests.get(game_url, headers=headers, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # Buscar información del juego desde la página principal
        game_info = extract_game_info(soup)

        # Buscar botón de descarga que redirige a página DLL
        download_button = soup.find('img', {'src': lambda x: x and 'Download-button' in x})

        if not download_button or not download_button.parent:
            if verbose:
                print(f"  ❌ No se encontró botón de descarga para {game_name}")
            return {}

        dll_url = download_button.parent.get('href')
        if not dll_url:
            if verbose:
                print(f"  ❌ Botón de descarga sin enlace válido para {game_name}")
            return {}

        # Convertir URL relativa a absoluta si es necesario
        dll_url = urljoin(game_url, dll_url)
        if verbose:
            print(f"  🔍 Página DLL: {dll_url}")

        # Extraer enlaces de la página DLL
        return extract_dll_page_links(dll_url, game_name, game_info, verbose)

    except Exception as e:
        if verbose:
            print(f"  ❌ Error procesando {game_name}: {e}")
        return {}

def save_server_files(all_server_data, test_mode=False):
    """Guarda los archivos separados por servidor"""
    saved_files = []

    # Preparar datos en formato FPKGi
    for server_name, server_data in all_server_data.items():
        if not server_data:  # Saltar servidores sin datos
            continue

        filename = f"{server_name}.json"
        if server_name == 'vikingfile':
            filename = "games.json"  # VikingFile es el archivo principal
        elif server_name == 'other':
            filename = "other_servers.json"

        # Formato FPKGi
        formatted_data = {"DATA": server_data}

        with open(filename, "w", encoding="utf-8") as f:
            json.dump(formatted_data, f, indent=2, ensure_ascii=False)

        saved_files.append(filename)
        print(f"💾 Guardado: {filename} con {len(server_data)} enlaces")

    return saved_files

def main():
    """Función principal del scraper"""
    parser = argparse.ArgumentParser(description='SuperPSX PS4 Scraper')
    parser.add_argument('--full', action='store_true', help='Procesar todos los juegos (modo producción)')
    parser.add_argument('--games', type=int, default=50, help='Número de juegos a procesar (default: 50)')
    parser.add_argument('--quiet', action='store_true', help='Modo silencioso (menos output)')

    args = parser.parse_args()

    verbose = not args.quiet
    test_mode = not args.full
    max_games = None if args.full else args.games

    if verbose:
        print("🚀 Iniciando SuperPSX PS4 Scraper - Versión Final")
        print(f"📊 Modo: {'PRODUCCIÓN (todos los juegos)' if args.full else f'PRUEBA ({max_games} juegos)'}")

    # Obtener lista de juegos desde GitHub
    github_json_url = "https://raw.githubusercontent.com/tutw/SuperPSX-PS4-GameList/refs/heads/main/ps4_games_list.json"

    try:
        if verbose:
            print(f"📡 Descargando lista de juegos desde GitHub...")
        response = requests.get(github_json_url, timeout=30)
        response.raise_for_status()
        data = response.json()

        games_list = data.get("games", [])
        total_games = len(games_list)

        if verbose:
            print(f"✅ Lista obtenida: {total_games} juegos disponibles")

    except Exception as e:
        print(f"❌ Error obteniendo lista de GitHub: {e}")
        return 1

    # Limitar juegos para modo prueba
    if test_mode and max_games:
        games_list = games_list[:max_games]
        if verbose:
            print(f"🧪 Modo prueba: procesando {len(games_list)} juegos")

    # Inicializar contadores por servidor
    all_server_data = {
        'vikingfile': {},
        'akirabox': {},
        '1fichier': {},
        'other': {}
    }

    processed = 0
    errors = 0
    total_links = 0

    if verbose:
        print(f"\n{'='*60}")
        print("🎯 INICIANDO SCRAPING...")
        print('='*60)

    for i, game in enumerate(games_list):
        name = game["name"]
        url = game["url"]

        try:
            # Extraer enlaces del juego
            server_links = extract_download_links(url, name, verbose)

            # Agregar enlaces a los datos globales por servidor
            for server_name, links in server_links.items():
                if links:  # Solo si hay enlaces
                    all_server_data[server_name].update(links)
                    total_links += len(links)

            processed += 1

        except Exception as e:
            if verbose:
                print(f"  ❌ Error general procesando {name}: {e}")
            errors += 1

        # Pausa entre requests para evitar rate limiting
        time.sleep(1.5)

        # Status cada 10 juegos
        if verbose and processed % 10 == 0:
            viking_count = len(all_server_data['vikingfile'])
            akira_count = len(all_server_data['akirabox'])
            fichier_count = len(all_server_data['1fichier'])
            other_count = len(all_server_data['other'])

            print(f"\n📊 PROGRESO ({processed}/{len(games_list)}):")
            print(f"  🏆 VikingFile: {viking_count} enlaces")
            print(f"  ⚡ AkiraBox: {akira_count} enlaces")
            print(f"  📁 1Fichier: {fichier_count} enlaces")
            print(f"  🌐 Otros: {other_count} enlaces")
            print(f"  ❌ Errores: {errors}")
            print("-" * 40)

    # Guardar resultados
    if verbose:
        print(f"\n{'='*60}")
        print("💾 GUARDANDO RESULTADOS...")
        print('='*60)

    saved_files = save_server_files(all_server_data, test_mode)

    # Estadísticas finales
    viking_count = len(all_server_data['vikingfile'])
    akira_count = len(all_server_data['akirabox'])
    fichier_count = len(all_server_data['1fichier'])
    other_count = len(all_server_data['other'])

    if verbose:
        print(f"\n🎉 SCRAPING COMPLETADO!")
        print(f"📈 Estadísticas finales:")
        print(f"  - Juegos procesados: {processed}")
        print(f"  - Errores: {errors}")
        print(f"  - Enlaces totales: {total_links}")
        print(f"  - VikingFile (principal): {viking_count}")
        print(f"  - AkiraBox: {akira_count}")
        print(f"  - 1Fichier: {fichier_count}")
        print(f"  - Otros servidores: {other_count}")
        print(f"  - Archivos generados: {', '.join(saved_files)}")

    # Calcular calidad
    success_rate = (processed / (processed + errors)) * 100 if (processed + errors) > 0 else 0
    quality_score = min(95, success_rate + (viking_count / processed * 10) if processed > 0 else 0)

    if verbose:
        print(f"\n🎯 CALIDAD DEL SCRAPING: {quality_score:.1f}/100")

        if quality_score >= 95:
            print("✅ ¡Excelente! El scraper funciona perfectamente.")
        elif quality_score >= 80:
            print("⚠️  Buena calidad, pero se puede mejorar.")
        else:
            print("❌ Necesita mejoras.")

    return 0 if quality_score >= 80 else 1

if __name__ == "__main__":
    exit(main())
