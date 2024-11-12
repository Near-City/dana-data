from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import base64
from descarga_datos import *
import json
import os
import time

token = get_token()
user_session = json.load(open("private/user.json")) 
user_session["accessToken"] = token

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
    time.sleep(1)  # Espera breve antes de ejecutar el JavaScript
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

def save_log(log, filename="log_informes_descargados.json"):
    with open(filename, "w") as f:
        json.dump(log, f)

def load_log(filename="log_informes_descargados.json"):
    if not os.path.exists(filename):
        return []
    with open(filename, "r") as f:
        return json.load(f)

def download_informes_group(driver, group_id, results=["RED"], base_folder="informes", log=None):
    time.sleep(5)
    driver.get(f"https://ctav.civilio.net/missions/{group_id}")
    tasks = get_group_tasks(token, group_id)  # Una única consulta a la API para obtener todas las tareas

    open_tasks_section(driver)
    try:
        for result in results:
            # Filtrar tareas para el resultado actual y crear la carpeta específica
            filtered_tasks = filter_tasks(tasks, result=result)
            folder = os.path.join(base_folder, result)
            os.makedirs(folder, exist_ok=True)

            amount = len(filtered_tasks)
            for i, task in enumerate(filtered_tasks):
                feature = (task.get("feature") or {})
                ref = feature.get("ref")
                if log is not None and ref in log:
                    print(f"({i}/{amount}) Tarea {ref} ya descargada.")
                    continue
                print(f"({i}/{amount}) Buscando tarea {ref} en {result}...")
                search_task(driver, ref)
                abrir_informe(driver)
                time.sleep(5)
                download_pdf_in_iframe(driver, f"{ref}.pdf", folder)
                close_informe(driver)
                if log is not None:
                    log.append(ref) 
                print(f"Tarea {ref} ({result}) descargada.")
                time.sleep(1)
        if log is not None:
            save_log(log)
    except Exception as e:
        print(e)
        if log is not None:
            save_log(log)
        
        

def download_informes_groups(driver, groups, results=["RED", "BLACK"], base_path="informes", log=None):
    for group in groups:
        path = os.path.join(base_path, group["name"])
        print(path)
        download_informes_group(driver, group["_id"], results=results, base_folder=path, log=log)

def main():
    driver = login()
    log = load_log() # registro de tareas descargadas
    groups = get_groups(token)
    download_informes_groups(driver, groups, log=log)
    driver.quit()

if __name__ == "__main__":
    main()