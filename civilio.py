import requests
from datetime import datetime
import json
import pandas as pd
import os

DATA_PATH = 'data/'
BASE_URL = 'https://ctav.civilio.net/api'
USERNAME = 'jcarot@eio.upv.es'
PASSWORD = '123456789'

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

def download_forms_results():
    token = get_token()
    all_data = []
    groups = get_groups(token)

    # Crear una carpeta con la fecha actual si no existe (AGRUPACIÓN DE CARPETAS POR DÍA) -> Varios ficheros de un día van en la misma carpeta
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
            json_data = json.loads(stringJson)
            flattened_data = _flatten_json(json_data)
            flattened_data['nombre_grupo'] = group_name
            all_data.append(flattened_data)

    df = pd.DataFrame(all_data)
    # Reordenar las columnas para que 'nombre_grupo' sea la primera
    columns = ['nombre_grupo'] + [col for col in df.columns if col != 'nombre_grupo']
    df = df[columns]

    df.to_csv(filename_csv, index=False)

#endregion

if __name__ == '__main__':
    os.makedirs(DATA_PATH, exist_ok=True) # Crear la carpeta 'data' si no existe
    download_forms_results()