import requests
from datetime import datetime
import json
import pandas as pd
import os
import git
import schedule
import time

DATA_PATH = "data"
STORAGE_PATH = "storage"
BASE_URL = "https://ctav.civilio.net/api"

credenciales = json.load(open("private/credenciales.json"))
USERNAME = credenciales["username"]
PASSWORD = credenciales["password"]


repo_path = os.path.dirname(os.path.abspath(__file__))
repo = git.Repo(repo_path)


def _flatten_json(json_data, prefix=""):
    items = {}
    for k, v in json_data.items():
        new_key = f"{prefix}.{k}" if prefix else k
        if isinstance(v, dict):
            items.update(_flatten_json(v, new_key))
        else:
            items[new_key] = v
    return items


def get_token():
    url = BASE_URL + "/auth/login"
    data = {"email": USERNAME, "password": PASSWORD}
    response = requests.post(url, data=data)
    try:
        response.raise_for_status()
        return response.json().get("accessToken")
    except requests.exceptions.HTTPError as e:
        print(e)
        return None


def request_data(token, endpoint, method="GET", data=None):
    url = BASE_URL + endpoint
    headers = {"Authorization": "Bearer " + token}
    response = requests.request(method, url, headers=headers, data=data)
    try:
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        print(e)
        return None


def get_groups(token, page=1, limit=30):
    response = (request_data(token, f"/groups?limit={limit}&page={page}") or {})
    groups, pagination = response.get("groups", []), response.get("pagination", {})
    if pagination.get("hasNextPage"):
        groups += get_groups(token, page=page + 1)
    return groups

def get_group_tasks_with_limit(token, group_id):
    print(f"Obteniendo tareas del grupo {group_id}")
    response = (
        request_data(token, f"/groups/{group_id}/tasks") or {}
    )
    tasks, pagination = response.get("tasks", []), response.get("pagination", {})
    if pagination.get("hasNextPage"):
        tasks += get_group_tasks_with_limit(token, group_id)
    return tasks



def filter_tasks(tasks, status=None, result=None):
    return [task for task in tasks if (status is None or task.get("_status") == status or task.get("status") == status) and (result is None or task.get("_result") == result or task.get("result") == result)]

# region Transformación datos
import numpy as np

import numpy as np

def transformar_df(df):
    # Reemplazo de valores booleanos por enteros
    df = df.replace({False: 0, True: 1})
    df['datosFachada.cotaAgua'] = df['datosFachada.cotaAgua'].apply(transform_cota_agua)
    # Nuevas variables - Sótano
    df["danos_Sotano"] = df[[
        "datosSotano.deformacion.danos", 
        "datosSotano.fisuras.danos", 
        "datosSotano.desprendimientos.danos", 
        "datosSotano.humedadAmbiente.danos",
        "datosSotano.instalacionesSaneamientos.danos",
        "datosSotano.instalacionesAbastecimientos.danos",
        "datosSotano.instalacionesElectricidad.danos",
        "datosSotano.instalacionesGas.danos"
    ]].sum(axis=1, min_count=1).fillna(0).astype(int)

    df["urgente_Sotano"] = df[[
        "datosSotano.deformacion.actuacion", 
        "datosSotano.fisuras.actuacion", 
        "datosSotano.desprendimientos.actuacion"
    ]].sum(axis=1, min_count=1).fillna(0).astype(int)
    
    df['urgente_Sotano_dicotomico'] = np.where(df['urgente_Sotano'] == 0, 0, 1).astype(int)
    
    # Nuevas variables - Planta Baja
    df["danos_PlantaBaja"] = df[[
        "datosPlantaBaja.deformacion.danos", 
        "datosPlantaBaja.fisuras.danos", 
        "datosPlantaBaja.accesibilidad.danos",
        "datosPlantaBaja.desprendimientos.danos", 
        "datosPlantaBaja.humedadAmbiente.danos",
        "datosPlantaBaja.instalacionesSaneamientos.danos",
        "datosPlantaBaja.instalacionesAbastecimientos.danos",
        "datosPlantaBaja.instalacionesElectricidad.danos",
        "datosPlantaBaja.instalacionesGas.danos"
    ]].sum(axis=1, min_count=1).fillna(0).astype(int)

    df["urgente_PlantaBaja"] = df[[
        "datosPlantaBaja.deformacion.actuacion", 
        "datosPlantaBaja.fisuras.actuacion", 
        "datosPlantaBaja.desprendimientos.actuacion"
    ]].sum(axis=1, min_count=1).fillna(0).astype(int)
    
    df['urgente_PlantaBaja_dicotomico'] = np.where(df['urgente_PlantaBaja'] == 0, 0, 1).astype(int)

    # Nuevas variables - Fachada
    df["danos_Fachada"] = df[[
        "datosFachada.seguridadCiudadana.danos",
        "datosFachada.deformacion.danos",
        "datosFachada.fisuras.danos",
        "datosFachada.fisuras.actuacion",
        "datosFachada.desprendimientos.danos",
        "datosFachada.instalacionesSaneamientos.danos",
        "datosFachada.instalacionesAbastecimientos.danos",
        "datosFachada.instalacionesElectricidad.danos",
        "datosFachada.instalacionesGas.danos"
    ]].sum(axis=1, min_count=1).fillna(0).astype(int)

    df["urgente_Fachada"] = df[[
        "datosFachada.deformacion.actuacion",
        "datosFachada.fisuras.actuacion",
        "datosFachada.desprendimientos.actuacion"
    ]].sum(axis=1, min_count=1).fillna(0).astype(int)
    
    df['urgente_Fachada_dicotomico'] = np.where(df['urgente_Fachada'] == 0, 0, 1).astype(int)

    # Nuevas variables - Perímetro
    df["danos_Perimetro"] = df[[
        "datosPerimetro.aceraPracticable", 
        "datosPerimetro.mobiliarioUrbano", 
        "datosPerimetro.vallado"
    ]].sum(axis=1, min_count=1).fillna(0).astype(int)

    # Nuevas variables - Operatividad
    df["no_Operativo"] = df[[
        "datosPlantaBaja.espaciosNoOperativos.cocina",
        "datosPlantaBaja.espaciosNoOperativos.banos",
        "datosPlantaBaja.espaciosNoOperativos.dormitorios",
        "datosPlantaBaja.espaciosNoOperativos.estar",
        "datosPlantaBaja.espaciosNoOperativos.exterior"
    ]].sum(axis=1, min_count=1).fillna(0).astype(int)

    # Nuevas variables - Totales
    df["danos_Total"] = (df["danos_PlantaBaja"] + df["danos_Sotano"] + df["danos_Fachada"]).fillna(0).astype(int)
    df["urgente_Total"] = (df["urgente_PlantaBaja"] + df["urgente_Sotano"] + df["urgente_Fachada"]).fillna(0).astype(int)
    df["IGD"] = (df["danos_Total"] + df["datosSotano.inundado"] + df["no_Operativo"] + df["datosFachada.seguridadCiudadana.danos"]).fillna(0).astype(int)

    # Conversiones explícitas de otros enteros
    df["numero"] = df["numero"].fillna(0).replace([np.inf, -np.inf], 0).astype(int)
    df["viviendas"] = df["viviendas"].fillna(0).replace([np.inf, -np.inf], 0).astype(int)

    # Asegurarse de no tener valores inválidos
    df = df.replace([np.inf, -np.inf], 0)
    df = df.fillna(0)

    df["tecnicos.fechaInspeccion"] = pd.to_datetime(df["tecnicos.fechaInspeccion"], errors="coerce")

    return df


def transform_cota_agua(value):
    
    if type(value) is float: # Es Float
        value = abs(value)  # Valor absoluto
        #SI está en un rango de entre 0,5 y 2,35, pasarlo a centimetros: e.g 1,65 -> 165
        entra = False
        if value == 1.9:
            entra = True
        if 0.5 <= value < 3:
            if entra:
                print(value * 100)
            return value * 100
        
        #Si está en un rango de Valores de 3 a 320, se mantienen
        if 3 <= value <= 320:
            return value
        
        return value
        
    value = value.replace(',', '.')  # Cambiar comas por puntos
    value = value.replace(' ', '')  # Eliminar espacios
    
    if '-' in value:  # Si es un rango
        try:
            parts = list(map(float, value.split('-')))
            return transform_cota_agua(sum(parts) / 2)  # Retornar el promedio del rango y aplicar la función
        except ValueError:
            return None  
    else:
        try:
            return transform_cota_agua(float(value))  # Convertir a float y aplicar la función
        except ValueError:
            return None  



#endregion

# region Funciones principales compuestas (Descargar formularios)



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
    amount = len(groups)
    amount_tasks = 0
    for i, group in enumerate(groups):
        group_name = group["name"]
        print(f"{i}/{amount} - Descargando datos del grupo {group_name}...")
        tasks = get_group_tasks_with_limit(token, group["_id"])
        completed_tasks = filter_tasks(tasks, status="FINISHED") # Tareas completadas
        pending_tasks = filter_tasks(tasks, status="PENDING") # Tareas pendientes
        in_progress_tasks = filter_tasks(tasks, status="IN PROGRESS") # Tareas pendientes
        tasks_of_interest = completed_tasks + pending_tasks + in_progress_tasks
        amount_tasks += len(completed_tasks)
        for completed_task in tasks_of_interest:
            task_data = {
                "nombre_grupo": group_name,
                "_id": completed_task.get("_id"),
                "groupId": completed_task.get("groupId"),
                "missionId": completed_task.get("missionId"),
                "userId": completed_task.get("userId"),
                "layerId": completed_task.get("layerId"),
                "featureId": completed_task.get("featureId"),
                "status": completed_task.get("status"),
                "result": completed_task.get("result"),
                "statusChangedAt": completed_task.get("statusChangedAt"),
                "resultChangedAt": completed_task.get("resultChangedAt"),
                "formChangedAt": completed_task.get("formChangedAt"),
                "createdAt": completed_task.get("createdAt"),
                "hasForm": True,
            }
            stringJson = completed_task.get("formData")
            flattened_formData = {}
            if not stringJson:
                print(
                    f"El formulario de la tarea {completed_task['_id']} del grupo {group_name} no tiene datos"
                )
                task_data["hasForm"] = False
            else:
                json_data = json.loads(stringJson)
                flattened_formData = _flatten_json(json_data)
            task_data["nombre_grupo"] = group_name

            #Extraer la información de `feature` y `properties`
            feature = completed_task.get('feature', {})
            
            # Aplanar las propiedades de `properties` dentro de `feature`
            properties = feature.get('properties', {})
            flattened_properties = _flatten_json(properties)

            # Combinar toda la información en un solo diccionario
            combined_data = {**task_data, **flattened_formData, **flattened_properties}
            all_data.append(combined_data)

    df = pd.DataFrame(all_data)
    # Reordenar las columnas para que 'nombre_grupo' sea la primera
    columns = ["nombre_grupo"] + [col for col in df.columns if col != "nombre_grupo"]
    df = df[columns]
    transformed_df = transformar_df(df)
    df.to_csv(filename_csv, index=False)
    transformed_df.to_csv(filename_csv.replace('.csv', '_transformed.csv'), index=False)
    print(f"Datos guardados en {filename_csv}")

    # Limpiar y mover archivos antiguos antes de subir a GitHub
    # clean_data_directory()

    if upload_to_github:
        upload_data(commit_message=f"Subida de datos del día {current_datetime}")

    print(f"Descarga finalizada. {amount_tasks} tareas completadas.")



# def clean_data_directory():
#     os.makedirs(STORAGE_PATH, exist_ok=True) # crear carpeta almacén si no existe

#     # listar archivos en data
#     all_files = []
#     for root, _, files in os.walk(DATA_PATH):
#         for file in files:
#             if file.endswith('.csv'):
#                 all_files.append(os.path.join(root, file))

#     # ordenar por fecha de modificación (los más antiguos primero)
#     all_files.sort(key=lambda x: os.path.getmtime(x))

#     # Mover archivos antiguos a `storage`, manteniendo solo los últimos 10
#     if len(all_files) > 10:
#         files_to_move = all_files[:-10]
#         for file_path in files_to_move:
#             relative_path = os.path.relpath(file_path, DATA_PATH)
#             storage_file_path = os.path.join(STORAGE_PATH, relative_path)
#             os.makedirs(os.path.dirname(storage_file_path), exist_ok=True)
#             os.rename(file_path, storage_file_path)  # Mover el archivo
#             print(f"Archivo movido a storage: {file_path}")


def upload_data(commit_message="Subida de datos"):
    # Subir los datos a un repositorio de GitHub
    repo.git.add(A=True)
    repo.index.commit(commit_message)
    origin = repo.remote(name="origin")
    origin.pull() # Actualizar el repositorio remoto
    origin.push()
    print("Datos subidos correctamente")


def ensure_storage_ignored():
    gitignore_path = ".gitignore"
    if os.path.exists(gitignore_path):
        with open(gitignore_path, "r") as f:
            lines = f.readlines()
        # Verifica si 'storage' ya está en .gitignore
        if any(STORAGE_PATH in line for line in lines):
            return  # Si ya está, no hace nada
    # Si no está en .gitignore, agrégalo
    with open(gitignore_path, "a") as f:
        f.write(f"\n{STORAGE_PATH}\n")


# endregion

ensure_storage_ignored()

if __name__ == "__main__":
    schedule.every().day.at("23:00").do(download_forms_results)  # Descargar los datos a las 20:00 cada día
    os.makedirs(DATA_PATH, exist_ok=True)  # Crear la carpeta 'data' si no existe
    os.makedirs(STORAGE_PATH, exist_ok=True)  # Crear la carpeta 'storage' si no existe

    while True:
        schedule.run_pending()
        time.sleep(1)

    # download_forms_results(upload_to_github=False)

