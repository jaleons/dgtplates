import io
import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from zipfile import ZipFile

# METER EN FUNCIÓN *********************************************************************************
# El cálculo de fechas lo haremos en función del último día que hayamos cargado en la base de datos
# **************************************************************************************************
# --- 1. Cálculo de fechas ---
# Obtener la fecha de hoy
today = datetime.now()

# Restar un día para obtener la fecha de ayer
yesterday = today - timedelta(days=1)

# Formatear la fecha de ayer en formato 'YYYYMMDD' para la convención de nombres de archivo de la DGT
yesterday_yyyymmdd = yesterday.strftime('%Y%m%d')

# Restar dos días para obtener la fecha de anteayer
day_before_yesterday = today - timedelta(days=2)

# Formatear la fecha de anteayer en formato 'YYYYMMDD'
day_before_yesterday_yyyymmdd = day_before_yesterday.strftime('%Y%m%d')

print(f"Fecha de hoy: {today.strftime('%Y-%m-%d')}")
print(f"Fecha de ayer: {yesterday.strftime('%Y-%m-%d')}")
print(f"Fecha de ayer formateada (YYYYMMDD): {yesterday_yyyymmdd}")
print(f"Fecha de anteayer: {day_before_yesterday.strftime('%Y-%m-%d')}")
print(f"Fecha de anteayer formateada (YYYYMMDD): {day_before_yesterday_yyyymmdd}")
# *********************************************************************************

# METER EN FUNCIÓN ****************************************************************
# --- 2. Raspar la página de la DGT para la URL del archivo ZIP (con respaldo) ---
# Definir la URL de la página de datos de registro de la DGT
dgt_url = 'https://www.dgt.es/menusecundario/dgt-en-cifras/matraba-listados/matriculaciones-automoviles-diario.html'
base_url = 'https://www.dgt.es'

# Enviar una solicitud HTTP GET a la URL de la DGT
response = requests.get(dgt_url)
response.raise_for_status() # Asegurarse de obtener una respuesta exitosa

# Analizar el contenido HTML de la respuesta usando BeautifulSoup
soup = BeautifulSoup(response.content, 'html.parser')
print("Se ha accedido correctamente a la página de la DGT y se ha analizado su contenido HTML.")

# Inicializar zip_file_url y txt_content
zip_file_url = None
txt_content = None

# Construir el patrón de búsqueda para el archivo ZIP de ayer
yesterday_search_pattern = re.compile(f'export_mat_{yesterday_yyyymmdd}.zip')

# Encontrar todas las etiquetas <a> con un atributo href
links = soup.find_all('a', href=True)

# Intentar encontrar la URL del archivo ZIP de ayer
for link in links:
    href = link['href']
    if yesterday_search_pattern.search(href):
        if href.startswith(base_url):
            zip_file_url = href
        else:
            zip_file_url = base_url + href
        break

# Si no se encontró el archivo ZIP de ayer, intentar con anteayer (Sólo para pruebas iniciales)
if not zip_file_url:
    print(f"No se encontró archivo ZIP para {yesterday_yyyymmdd}. Intentando con {day_before_yesterday_yyyymmdd}...")
    day_before_yesterday_search_pattern = re.compile(f'export_mat_{day_before_yesterday_yyyymmdd}.zip')
    for link in links:
        href = link['href']
        if day_before_yesterday_search_pattern.search(href):
            if href.startswith(base_url):
                zip_file_url = href
            else:
                zip_file_url = base_url + href
            break

# Imprimir el resultado de la búsqueda de URL
if zip_file_url:
    print(f"URL del archivo ZIP corregida encontrada: {zip_file_url}")
    # --- 3. Descargar y extraer TXT del ZIP ---
    print(f"Descargando archivo ZIP de: {zip_file_url}")
    zip_response = requests.get(zip_file_url)
    zip_response.raise_for_status() # Lanzar una excepción para errores HTTP

    with io.BytesIO(zip_response.content) as zip_buffer:
        with ZipFile(zip_buffer, 'r') as zf:
            file_names = zf.namelist()
            txt_file_name = None
            for fname in file_names:
                if fname.endswith('.txt'):
                    txt_file_name = fname
                    break

            if txt_file_name:
                print(f"Archivo TXT encontrado en el ZIP: {txt_file_name}")
                with zf.open(txt_file_name) as txt_file:
                    txt_content = txt_file.read().decode('latin-1')
                print("Contenido del archivo TXT cargado exitosamente en la variable 'txt_content'.")
            else:
                print("No se encontró ningún archivo TXT dentro del archivo ZIP descargado.")
                txt_content = None # Asegurarse de que sea None si no se encuentra TXT en el ZIP
else:
    print("No se encontró ninguna URL de archivo ZIP para ayer o anteayer en la página de la DGT. No se puede proceder con la descarga.")
    txt_content = None # Asegurarse de que sea None si no se encuentra URL de ZIP

# --- 4. Mostrar el contenido TXT extraído ---
if txt_content:
    # Limito la impresión a sólo 500 caracteres sólo para comprobar que se ha leído correctamente
    print("\n--- Contenido TXT extraído (primeros 500 caracteres) ---")
    print(txt_content[:500])
else:
    print("\nNo hay contenido para mostrar, ya que no se encontró ningún archivo ZIP o no se extrajo ningún archivo TXT.")

# --- 5. Cargamos los datos leídos en la Base de Datos que vayamos a usar
# Importante considerar tabla de taxonomía para Normalizar la Marca y el Modelo del vehículo