import requests
from datetime import datetime
import json
import pandas as pd
import os
import git
import schedule
import time

DATA_PATH = 'data'
STORAGE_PATH = 'storage'
BASE_URL = 'https://ctav.civilio.net/api'
USERNAME = 'jcarot@eio.upv.es'
PASSWORD = '123456789'

repo_path = os.path.dirname(os.path.abspath(__file__))
repo = git.Repo(repo_path)

def _flatten_json(json_data, prefix=''):
    items = {}
    for k, v in json_data.items():
        new_key = f"{prefix}.{k}" if prefix else k
        if isinstance(v, dict):
            items.update(_flatten_json(v, new_key))
        else:
            items[new_key] = v
    return items


def get_token():
    url = BASE_URL + '/auth/login'
    data = {
        'email': USERNAME,
        'password': PASSWORD
    }
    response = requests.post(url, data=data)
    try:
        response.raise_for_status()
        return response.json().get('accessToken')
    except requests.exceptions.HTTPError as e:
        print(e)
        return None
    
def request_data(token, endpoint, method='GET', data=None):
    url = BASE_URL + endpoint
    headers = {
        'Authorization': 'Bearer ' + token
    }
    response = requests.request(method, url, headers=headers, data=data)
    try:
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        print(e)
        return None
    
def get_groups(token):
    return (request_data(token, '/groups') or {}).get('groups', [])

def get_group_tasks(token, group_id):
    return (request_data(token, f'/groups/{group_id}/tasks') or {}).get('tasks', [])

def filter_tasks(tasks, status):
    return [task for task in tasks if task.get('status') == status]


#region Funciones principales compuestas (Descargar formularios)

def download_forms_results(upload_to_github=True):
    print("Descargando datos...")
    token = get_token()
    all_data = []
    groups = get_groups(token)

    # Crear una carpeta con la fecha actual si no existe (AGRUPACIÓN DE CARPETAS POR DÍA)
    current_day = datetime.now().strftime("%Y-%m-%d")
    day_data_path = os.path.join(DATA_PATH, current_day)
    os.makedirs(day_data_path, exist_ok=True)

    # Obtener la fecha y hora actual en formato yyyy-mm-dd_HH-MM-SS
    current_datetime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename_csv = f"{current_datetime}.csv"
    filename_csv = os.path.join(day_data_path, filename_csv)
    
    for group in groups:
        group_name = group['name']
        tasks = get_group_tasks(token, group['_id'])
        completed_tasks = filter_tasks(tasks, status='FINISHED')
        for completed_task in completed_tasks:
            stringJson = completed_task.get('formData')
            if not stringJson:
                print(f"El formulario de la tarea {completed_task['_id']} no tiene datos")
                continue
            json_data = json.loads(stringJson)
            flattened_data = _flatten_json(json_data)
            flattened_data['nombre_grupo'] = group_name
            all_data.append(flattened_data)

    df = pd.DataFrame(all_data)
    # Reordenar las columnas para que 'nombre_grupo' sea la primera
    columns = ['nombre_grupo'] + [col for col in df.columns if col != 'nombre_grupo']
    df = df[columns]

    df.to_csv(filename_csv, index=False)
    print(f"Datos guardados en {filename_csv}")
    
    # Limpiar y mover archivos antiguos antes de subir a GitHub
    clean_data_directory()

    if upload_to_github:
        upload_data(commit_message=f"Subida de datos del día {current_datetime}")
    

def clean_data_directory():
    os.makedirs(STORAGE_PATH, exist_ok=True) # crear carpeta almacén si no existe
    
    # listar archivos en data
    all_files = []
    for root, _, files in os.walk(DATA_PATH):
        for file in files:
            if file.endswith('.csv'):
                all_files.append(os.path.join(root, file))

    # ordenar por fecha de modificación (los más antiguos primero)
    all_files.sort(key=lambda x: os.path.getmtime(x))

    # Mover archivos antiguos a `storage`, manteniendo solo los últimos 10
    if len(all_files) > 10:
        files_to_move = all_files[:-10]
        for file_path in files_to_move:
            relative_path = os.path.relpath(file_path, DATA_PATH)
            storage_file_path = os.path.join(STORAGE_PATH, relative_path)
            os.makedirs(os.path.dirname(storage_file_path), exist_ok=True)
            os.rename(file_path, storage_file_path)  # Mover el archivo
            print(f"Archivo movido a storage: {file_path}")

def upload_data(commit_message="Subida de datos"):
    # Subir los datos a un repositorio de GitHub
    repo.git.add(A=True)
    repo.index.commit(commit_message)
    origin = repo.remote(name='origin')
    origin.push()
    print("Datos subidos correctamente")

def ensure_storage_ignored():
    gitignore_path = '.gitignore'
    if os.path.exists(gitignore_path):
        with open(gitignore_path, 'r') as f:
            lines = f.readlines()
        # Verifica si 'storage' ya está en .gitignore
        if any(STORAGE_PATH in line for line in lines):
            return  # Si ya está, no hace nada
    # Si no está en .gitignore, agrégalo
    with open(gitignore_path, 'a') as f:
        f.write(f'\n{STORAGE_PATH}\n')

#endregion

ensure_storage_ignored()

if __name__ == '__main__':
    # schedule.every().day.at("17:00").do(download_forms_results)  # Descargar los datos a las 20:00 cada día
    # os.makedirs(DATA_PATH, exist_ok=True)  # Crear la carpeta 'data' si no existe
    # os.makedirs(STORAGE_PATH, exist_ok=True)  # Crear la carpeta 'storage' si no existe
    
    # while True:
    #     schedule.run_pending()
    #     time.sleep(1)
    download_forms_results()  # Descargar los datos ahora
