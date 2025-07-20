# 🎮 SuperPSX PS4 Scraper

Extractor automatizado de enlaces de descarga de juegos PS4 desde SuperPSX.com con soporte para GitHub Actions.

## 🎯 Características

✅ **Scraping automatizado** - Procesa 1781 juegos PS4  
✅ **Prioridades de servidores** - VikingFile > AkiraBox > 1Fichier  
✅ **Clasificación automática** - Juegos, Updates y DLC separados  
✅ **Formato FPKGi** - Compatible con FPKGi homebrew app  
✅ **GitHub Actions** - Ejecución automática 2x día + manual  
✅ **Extracción de metadatos** - Región, versión, tamaño, cover, etc.  

## 📁 Estructura de archivos

```
├── ps4_games_list.json      # Lista de juegos de entrada (requerido)
├── scrape_superpsx.py       # Script principal de scraping  
├── .github/workflows/       
│   └── scraper.yml          # GitHub Actions workflow
├── games.json               # Salida: Enlaces de juegos base
├── updates.json             # Salida: Enlaces de updates  
├── DLC.json                 # Salida: Enlaces de DLC
└── README.md                # Este archivo
```

## 🚀 Uso Local

### Prerrequisitos
```bash
python >= 3.8
pip install -r requirements.txt
```

### Ejecución
```bash
# 1. Coloca ps4_games_list.json en la raíz
# 2. Ejecuta el scraper
python scrape_superpsx.py
```

## ⚙️ GitHub Actions (Recomendado)

### Configuración inicial:
1. **Fork este repositorio**
2. **Sube ps4_games_list.json** a la raíz del repositorio
3. **Activa GitHub Actions** en Settings > Actions > General

### Ejecución automática:
- ⏰ **Programado**: 2 veces al día (6 AM y 6 PM UTC)
- 🔄 **Manual**: Ve a Actions > "SuperPSX PS4 Scraper" > Run workflow

### Resultados:
Los archivos JSON se actualizarán automáticamente en el repositorio y estarán disponibles como artefactos.

## 📊 Formato de salida

### games.json / updates.json / DLC.json
```json
{
  "DATA": {
    "https://vikingfile.com/f/abc123": {
      "region": "USA",
      "name": "Assassin's Creed Mirage", 
      "version": "1.00",
      "release": "October 5, 2023",
      "size": "21.74 GB",
      "min_fw": "10.71+",
      "cover_url": "https://..."
    }
  }
}
```

## 🎯 Servidores soportados

| Prioridad | Servidor | Ejemplo |
|-----------|----------|---------|
| 🟢 **1** | VikingFile | `https://vikingfile.com/f/...` |
| 🟠 **2** | AkiraBox | `https://akirabox.com/.../file` |
| 🟡 **3** | 1Fichier | `https://1fichier.com/?...` |

❌ **Excluye**: filecrypt.cc

## 🔧 Personalización

### Modificar frecuencia (GitHub Actions):
Edita `.github/workflows/scraper.yml`:
```yaml
schedule:
  - cron: '0 */6 * * *'  # Cada 6 horas
```

### Cambiar servidores:
Modifica la función `extract_dll_page_links()` en `scrape_superpsx.py`

## 🐛 Solución de problemas

### Error 404:
- Verifica que `ps4_games_list.json` esté en la raíz
- Comprueba el formato del archivo JSON

### Rate limiting:
- El script incluye delays automáticos entre requests
- GitHub Actions reinicia si hay timeout

### Errores de scraping:
- Revisa los logs en GitHub Actions
- Algunos juegos pueden no tener enlaces disponibles

## 📝 Log de ejemplo

```
🚀 Iniciando SuperPSX PS4 Scraper
📋 Procesando 1781 juegos...
Procesando: 10 Second Ninja X
  🔗 Página DLL encontrada: https://www.superpsx.com/dll-10snx/
  🟢 VikingFile encontrado: https://vikingfile.com/f/...
  🟠 AkiraBox encontrado: https://akirabox.com/.../file
📊 Progreso: 10 juegos procesados, 0 errores
...
✅ Scraping completado!
📈 Estadísticas finales:
  - Juegos procesados: 1781
  - Errores: 12
  - Enlaces de juegos: 4532
  - Enlaces de updates: 892  
  - Enlaces de DLC: 234
```

## 🤝 Contribuciones

1. Fork el repositorio
2. Crea una rama para tu feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit tus cambios (`git commit -am 'Añadir nueva funcionalidad'`)  
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Abre un Pull Request

## 📄 Licencia

Este proyecto es de código abierto. Úsalo responsablemente y respeta los términos de uso de SuperPSX.com.

## ⚠️ Descargo de responsabilidad

Este scraper es solo para fines educativos y de preservación. No nos hacemos responsables del uso indebido de los enlaces extraídos. Siempre respeta las leyes locales y los términos de servicio.
