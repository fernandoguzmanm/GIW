"""
TODO: rellenar

Asignatura: GIW
Práctica 2
Grupo: XXXXXXX
Autores: XXXXXX 

Declaramos que esta solución es fruto exclusivamente de nuestro trabajo personal. No hemos
sido ayudados por ninguna otra persona o sistema automático ni hemos obtenido la solución
de fuentes externas, y tampoco hemos compartido nuestra solución con otras personas
de manera directa o indirecta. Declaramos además que no hemos realizado de manera
deshonesta ninguna otra actividad que pueda mejorar nuestros resultados ni perjudicar los
resultados de los demás.
"""


### Formato CSV
import csv
def lee_fichero_accidentes(ruta):
    #vamos a leer el fichero usando csv.DictReader para que nos devuelva
    #un diccionario por cada fila y poder acceder a cada elemento por clave

    #como necesitamos devolver una lista de diccionarios crearemos una lista
    #a la que iremos añadiendo las líneas leídas como diccionarios en el fichero

    lista_accidentes = []

    with open(ruta, 'r', newline='', encoding='utf8') as fich:
        #aquí como el delimitador correcto es ; y no , que es el predeterminado de csv hay que cambiarlo con delimiter
        lector = csv.DictReader(fich, delimiter=';')
        for linea in lector:
            lista_accidentes.append(linea)
    return lista_accidentes

def accidentes_por_distrito_tipo(datos):
    #función que devuelve un diccionario pasando el de lee_fichero_accidentes
    #devolviendo otro diccionario que contée los accidentes por distrito
    dicc_sol = {}

    for item in datos:
        #estandarizamos el texto a la salida buscada por el ejercicio
        distrito = item['distrito'].strip().upper()
        tipo = item['tipo_accidente'].strip()

        clave = (distrito, tipo)

        #si ya existe la clave en nuestro diccionario añadiremos un accidente
        #como valor, de lo contrario, lo añadiremos al diccionario con un 1
        if clave in dicc_sol:
            dicc_sol[clave] += 1
        else:
            dicc_sol[clave] = 1
    #devolveremos el diccionario generado
    return dicc_sol

def dias_mas_accidentes(datos):
    dicc_fechas = {}

    for item in datos:
        fecha = item['fecha'].strip()
        dicc_fechas[fecha] = dicc_fechas.get(fecha, 0) + 1

    # máximo número de accidentes en un día
    max_acc = max(dicc_fechas.values())

    # devolvemos todas las fechas con ese número de accidentes
    dias_maximos = [fecha for fecha, n in dicc_fechas.items() if n == max_acc]

    return dias_maximos

def puntos_negros_distrito(datos, distrito, k):
    distrito = distrito.strip().upper()
    conteo = {}

    for item in datos:
        if item['distrito'].strip().upper() == distrito:
            punto = item.get('localizacion', item.get('direccion', '')).strip()
            conteo[punto] = conteo.get(punto, 0) + 1

    # ordenamos los puntos por número de accidentes (descendente)
    puntos_ordenados = sorted(conteo.items(), key=lambda x: x[1], reverse=True)

    # devolvemos los k primeros puntos
    return puntos_ordenados[:k]


#### Formato JSON

#Ejercicio 1 JSON 
import json
def leer_monumentos(ruta):
    """
    Lee el fichero JSON que contiene la información de los monumentos de Madrid 
    y devuelve una lista de diccionarios, uno por cada monumento

    """
    with open(ruta, "r", encoding="utf-8") as fichero: #abrimos fichero en modo lectura con codificación UTF-8, con el with garantizamos que se cierre el archivo al terminar
        datos = json.load(fichero)  #lee contenido y convierte en estructura de python 
    #la lista de monumentos está dentro de la clave @graph
    return datos["@graph"]

def codigos_postales(monumentos):
    """
    devuelve lista de parejas con el numero total de documentos que hay en cada codigo postal 

    """
    contador = {} #creamos contador para mantener el orden 

    for m in monumentos: 
        #extraemos codigo postal, en el caso de que no exista, usamos cadena vacia 
        codigo_postal = m.get("address", {}).get("postal-code", "")
        contador[codigo_postal] = contador.get(codigo_postal, 0) +1

    #convertimos el contador a la lista de tuplas 
    lista_codigos = list(contador.items())

    #ordenamos primero por numero de monumentos
    lista_codigos.sort(key=lambda x: x[1], reverse=True)

    return lista_codigos


# Ejercicio 3 JSON
def busqueda_palabras_clave(monumentos, palabras):
    """
    Devuelve un conjunto de parejas (titulo, distrito_url) con los monumentos
    cuyo título o descripción contienen TODAS las palabras clave (como subcadenas,
    sin distinguir mayúsculas/minúsculas). Si no existe district -> '@id',
    el distrito será ''.

    Parámetros:
        monumentos: lista de diccionarios (cada monumento)
        palabras: lista de cadenas con palabras clave

    Retorno:
        set[tuple[str, str]]
    """
    # Normalizamos y filtramos palabras vacías o no cadena
    claves = [p.strip().casefold() for p in palabras if isinstance(p, str) and p.strip()]
    resultado = set()

    if not claves:
        return resultado

    for m in monumentos:
        # Extraer título y descripción (si faltan, usar cadena vacía)
        titulo = str(m.get("title", ""))
        desc = str(m.get("organization", {}).get("organization-desc", ""))

        # Texto combinado en minúsculas "robustas" (casefold maneja Unicode)
        texto = (titulo + " " + desc).casefold()

        # Deben aparecer TODAS las palabras como subcadenas
        if all(clave in texto for clave in claves):
            # district -> '@id' o '' si no existe
            district_url = ""
            addr = m.get("address", {})
            dist_obj = addr.get("district", {})
            if isinstance(dist_obj, dict):
                district_url = dist_obj.get("@id", "") or ""

            resultado.add((titulo, district_url))

    return resultado

# Ejercicio 4 JSON
from geopy.geocoders import Nominatim
from geopy.distance import geodesic

def busqueda_distancia(monumentos, direccion, distancia):
    """
    Devuelve una lista de ternas (título, id, distancia en km) de los monumentos
    que se encuentran a menos de 'distancia' km desde la 'direccion' pasada.
    La lista está ordenada de más cercano a lejano, preservando el orden original
    en caso de empate en distancia. Ignora monumentos sin información de localización.

    Parámetros:
        monumentos: lista de diccionarios (cada monumento)
        direccion: cadena con la dirección de referencia
        distancia: número (en km) máximo para filtrar

    Retorno:
        list[tuple[str, str, float]]
    """
    # Creamos el geocodificador con el user_agent requerido
    geolocator = Nominatim(user_agent="GIW_pr2")
    
    # Obtenemos lat/lon de la dirección; si falla, devolvemos lista vacía
    location = geolocator.geocode(direccion)
    if not location:
        return []
    
    # Punto de referencia: (latitud, longitud) -- orden importante para geodesic
    ref_point = (location.latitude, location.longitude)
    
    # Lista de candidatos: recolectamos en orden de aparición para preservar en empates
    candidatos = []
    
    for mon in monumentos:
        # Extraemos título e ID de forma segura
        titulo = mon.get("title", "")
        mon_id = mon.get("id", "")
        
        if not titulo or not mon_id:  # Saltamos si faltan datos básicos
            continue
        
        # Extraemos lat/lon del monumento de forma anidada y segura
        location_mon = mon.get("location", {})
        lat = location_mon.get("latitude")
        lon = location_mon.get("longitude")
        
        # Ignoramos si no hay lat/lon válida (como indica el enunciado)
        if lat is None or lon is None:
            continue
        
        try:
            # Convertimos a float y calculamos distancia con geodesic
            mon_point = (float(lat), float(lon))
            dist_km = geodesic(ref_point, mon_point).km
            
            # Si está dentro del radio, añadimos la terna
            if dist_km < distancia:
                candidatos.append((titulo, mon_id, dist_km))
        except (ValueError, TypeError):
            continue
    
    # Ordenamos por distancia ascendente: sorted() es estable, preserva orden original en empates
    candidatos.sort(key=lambda x: x[2])
    
    return candidatos

    

# =========================
# PRUEBAS DEL CÓDIGO
# =========================

#leer fichero csv -> indicar ruta propia del fichero csv para su lectura
mi_lista_accidentes = lee_fichero_accidentes("D:/AA_DatosUsb/AA_SegundoUSB/GIW/Practica_2/AccidentesBicicletas_2021.csv")
#compruebo la primera lectura del fichero imprimiendo la línea 0
print(mi_lista_accidentes[0])

#comprobamos la segunda función
accidentes_distrito_tipo = accidentes_por_distrito_tipo(mi_lista_accidentes)
print(accidentes_distrito_tipo)

print(dias_mas_accidentes(mi_lista_accidentes))
print(puntos_negros_distrito(mi_lista_accidentes, "CENTRO", 5))


#pruebas json 
#1
monumentos = leer_monumentos("300356-0-monumentos-ciudad-madrid.json")
print(len(monumentos))  #vemos cuantos hay 
print(monumentos[0].keys()) #vemos claves del primer monumento 
print(monumentos[0]["title"]) #vemos el título del primer monumento 

#2 
print(type(monumentos), len(monumentos), type(monumentos[0]))
res = codigos_postales(monumentos)
print(res[:10])

#3 (Ejercicio 3) - PRUEBAS JSON
#   Probamos con distintas combinaciones de palabras clave.
#   Mostramos tamaño del resultado y algunas coincidencias ordenadas por título para reproducibilidad.

# 3.a) Búsqueda de una palabra suelta (ej.: "museo")
palabras_1 = ["museo"]
res_busq_1 = busqueda_palabras_clave(monumentos, palabras_1)
print("E3-1 | claves =", palabras_1, "| encontrados:", len(res_busq_1))
print(sorted(list(res_busq_1))[:10])  # primeras 10 parejas (titulo, distrito_url)

# 3.b) Dos palabras que deben aparecer ambas (ej.: "plaza" y "reina")
palabras_2 = ["plaza", "reina"]
res_busq_2 = busqueda_palabras_clave(monumentos, palabras_2)
print("E3-2 | claves =", palabras_2, "| encontrados:", len(res_busq_2))
print(sorted(list(res_busq_2))[:10])

# 3.c) Palabras con mayúsculas/minúsculas mezcladas (comprobación case-insensitive)
palabras_3 = ["PuEnTe", "HISTÓRICO"]
res_busq_3 = busqueda_palabras_clave(monumentos, palabras_3)
print("E3-3 | claves =", palabras_3, "| encontrados:", len(res_busq_3))
print(sorted(list(res_busq_3))[:10])

# 3.d) Palabras con espacios y entradas vacías (se ignoran vacíos)
palabras_4 = ["  jardín  ", "", "botánico"]
res_busq_4 = busqueda_palabras_clave(monumentos, palabras_4)
print("E3-4 | claves =", palabras_4, "| encontrados:", len(res_busq_4))
print(sorted(list(res_busq_4))[:10])


