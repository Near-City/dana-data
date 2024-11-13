import pandas as pd
import numpy as np


df_12_11 = pd.read_csv(r"C:\Users\aidaa\OneDrive\Escritorio\DANA_analisis\Datos\2024-11-12_23-00-01.csv", sep=",")

df_new = df_12_11.replace({False:0, True:1})

#NUEVAS VARIABLES SOTANO
df_new["danos_Sotano"] = df_new[["datosSotano.deformacion.danos", 
                                 "datosSotano.fisuras.danos", 
                                 "datosSotano.desprendimientos.danos", 
                                 "datosSotano.humedadAmbiente.danos",
                                 "datosSotano.instalacionesSaneamientos.danos",
                                 "datosSotano.instalacionesAbastecimientos.danos",
                                 "datosSotano.instalacionesElectricidad.danos",
                                 "datosSotano.instalacionesGas.danos"]].sum(axis=1)

df_new["urgente_Sotano"] = df_new[["datosSotano.deformacion.actuacion", 
                                   "datosSotano.fisuras.actuacion", 
                                   "datosSotano.desprendimientos.actuacion"]].sum(axis=1)

#NUEVAS VARIABLES PLANTA BAJA
df_new["danos_PlantaBaja"] = df_new[["datosPlantaBaja.deformacion.danos", 
                                     "datosPlantaBaja.fisuras.danos", 
                                     "datosPlantaBaja.accesibilidad.danos",
                                     "datosPlantaBaja.desprendimientos.danos", 
                                     "datosPlantaBaja.humedadAmbiente.danos",
                                     "datosPlantaBaja.instalacionesSaneamientos.danos",
                                     "datosPlantaBaja.instalacionesAbastecimientos.danos",
                                     "datosPlantaBaja.instalacionesElectricidad.danos",
                                     "datosPlantaBaja.instalacionesGas.danos"]].sum(axis=1)

df_new["urgente_PlantaBaja"] = df_new[["datosPlantaBaja.deformacion.actuacion", 
                                   "datosPlantaBaja.fisuras.actuacion", 
                                   "datosPlantaBaja.desprendimientos.actuacion"]].sum(axis=1)

#NUEVAS VARIABLES FACHADA
df_new["danos_Fachada"] = df_new[["datosFachada.seguridadCiudadana.danos",
                                  "datosFachada.deformacion.danos",
                                  "datosFachada.fisuras.danos",
                                  "datosFachada.fisuras.actuacion",
                                  "datosFachada.desprendimientos.danos",
                                  "datosFachada.instalacionesSaneamientos.danos",
                                  "datosFachada.instalacionesAbastecimientos.danos",
                                  "datosFachada.instalacionesElectricidad.danos",
                                  "datosFachada.instalacionesGas.danos"]].sum(axis=1)

df_new["urgente_Fachada"] = df_new[["datosFachada.deformacion.actuacion",
                                    "datosFachada.fisuras.actuacion",
                                    "datosFachada.desprendimientos.actuacion"]].sum(axis=1)

#NUEVAS VARIABLES PERIMETRO
df_new["danos_Perimetro"] = df_new[["datosPerimetro.aceraPracticable","datosPerimetro.mobiliarioUrbano", "datosPerimetro.vallado"]].sum(axis=1)

#NUEVAS VARIABLES OPERATIVIDAD
df_new["no_Operativo"] = df_new[["datosPlantaBaja.espaciosNoOperativos.cocina",
                                 "datosPlantaBaja.espaciosNoOperativos.banos",
                                 "datosPlantaBaja.espaciosNoOperativos.dormitorios",
                                 "datosPlantaBaja.espaciosNoOperativos.estar",
                                 "datosPlantaBaja.espaciosNoOperativos.exterior"]].sum(axis=1)

#NUEVAS VARIABLES URGENTE
df_new["DEF_Urgente"] = df_new[["datosSotano.deformacion.actuacion", 
                               "datosPlantaBaja.deformacion.actuacion",
                               "datosFachada.deformacion.actuacion"]].sum(axis=1)
df_new['DEF_dicotomico'] = np.where(df_new['DEF_Urgente']==0, 0, 1)

df_new["FIS_Urgente"] = df_new[["datosSotano.fisuras.actuacion", 
                               "datosPlantaBaja.fisuras.actuacion",
                               "datosFachada.fisuras.actuacion"]].sum(axis=1)
df_new['FIS_dicotomico'] = np.where(df_new['FIS_Urgente']==0, 0, 1)

df_new["DES_Urgente"] = df_new[["datosSotano.desprendimientos.actuacion", 
                               "datosPlantaBaja.desprendimientos.actuacion",
                               "datosFachada.desprendimientos.actuacion"]].sum(axis=1)
df_new['DES_dicotomico'] = np.where(df_new['DES_Urgente']==0, 0, 1)

#NUEVAS VARIABLES TOTALES
df_new["danos_Total"] = df_new["danos_PlantaBaja"] + df_new["danos_Sotano"] + df_new["danos_Fachada"]
df_new["urgente_Total"] = df_new["urgente_PlantaBaja"] + df_new["urgente_Sotano"] + df_new["urgente_Fachada"]
df_new["IGD"] = df_new["danos_Total"] + df_new["datosSotano.inundado"] + df_new["no_Operativo"] + df_new["datosFachada.seguridadCiudadana.danos"]

df_new.to_csv(r"C:\Users\aidaa\OneDrive\Escritorio\DANA_analisis\Datos\test_tableau.csv", sep=";")