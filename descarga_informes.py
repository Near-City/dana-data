from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import base64
from civilio import *
import json
import os
import time

token = get_token()
user_session = {
    "_id": "672f842b27d61b402286f1e9",
    "name": "José Miguel Carot Sierra",
    "email": "jcarot@eio.upv.es",
    "age": 0,
    "roles": ["ROLE_COORDINATOR", "ROLE_INSPECTOR"],
    "accessToken": token,
    "lastLoginAt": "2024-11-11T18:59:06.149Z",
    "createdAt": "2024-11-09T15:47:55.648Z",
    "entity": {
        "_id": "672f83e327d61b402286f01a",
        "name": "UPV",
        "email": "jcarot@eio.upv.es",
        "phone": "+34 696 79 89 63"
    },
    "frontConfig": {
        "app": {
            "title": "Civilio -> CTAV",
            "itemsListLimit": 20
        },
        "map": {
            "center": [39.422775, -0.402108],
            "zoom": 16,
            "scrollWheelZoom": True
        },
        "disk": {
            "usageMaxSize": 1024,
            "usageSize": "2003.91"
        }
    }
}


def login():
    # Convertimos el diccionario a un string JSON
    user_session_json = json.dumps(user_session)

    # Configuración del navegador
    options = webdriver.ChromeOptions()
    driver = webdriver.Chrome()
    driver.get("https://ctav.civilio.net/")

    # Navega a la página y realiza el proceso necesario para abrir el modal con el PDF
    driver.execute_script(f"window.localStorage.setItem('user', '{user_session_json}');")
    driver.refresh()
    return driver


def open_tasks_section(driver):
    tasks_btn = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "missions-tab-panel-tab-tasklist"))
    )

    tasks_btn.click()

def search_task(driver, task_id):
    search_input = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.NAME, "search"))
    )
    # Limpiamos el input
    search_input.clear()

    search_input.send_keys(task_id)

def abrir_informe(driver):
    time.sleep(2)  # Espera breve antes de buscar el elemento

    informe_btn = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//td/div/button[2]"))
    )
    informe_btn.click()

def download_pdf_in_iframe(driver, filename = "informe.pdf", folder = None):
    # Espera a que el modal y el iframe con el PDF estén visibles
    WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.TAG_NAME, "iframe")))

    # Encuentra el iframe y obtiene su src (URL del Blob)
    iframe = driver.find_element(By.TAG_NAME, "iframe")
    blob_url = iframe.get_attribute("src")
    time.sleep(3)  # Espera breve antes de ejecutar el JavaScript
    # Ejecuta JavaScript para obtener el contenido del Blob como base64
    pdf_data_base64 = driver.execute_script("""
        return fetch(arguments[0])
            .then(response => response.blob())
            .then(blob => new Promise((resolve, reject) => {
                const reader = new FileReader();
                reader.onloadend = () => resolve(reader.result.split(',')[1]);
                reader.onerror = reject;
                reader.readAsDataURL(blob);
            }));
    """, blob_url)

    # Decodifica y guarda el PDF
    if pdf_data_base64:
        pdf_data = base64.b64decode(pdf_data_base64)
        if folder:
            os.makedirs(folder, exist_ok=True)
            filename = os.path.join(folder, filename)
        with open(filename, "wb") as f:
            f.write(pdf_data)
        print("El archivo PDF ha sido descargado.")
    else:
        print("No se pudo descargar el archivo PDF.")

def close_informe(driver):
    close_btn = driver.find_element(By.CLASS_NAME, "btn-close")
    close_btn.click()