"""
TODO: rellenar

Asignatura: GIW
Práctica 4
Grupo: 3
Autores: Pablo Bernal Calleja
         Fernando Guzmán Muñoz
         Álvaro González-Barros Medina
         Guillermo Guzmán González Ortíz
         Nicolás López-Chaves Pérez

Declaramos que esta solución es fruto exclusivamente de nuestro trabajo personal. No hemos
sido ayudados por ninguna otra persona o sistema automático ni hemos obtenido la solución
de fuentes externas, y tampoco hemos compartido nuestra solución con otras personas
de manera directa o indirecta. Declaramos además que no hemos realizado de manera
deshonesta ninguna otra actividad que pueda mejorar nuestros resultados ni perjudicar los
resultados de los demás.
"""

import sqlite3
import csv
from datetime import datetime


def crear_bd(db_filename):
    """
    Crea una base de datos en el fichero db_filename y define las tablas datos_generales
    y semanales_IBEX35 con sus claves primarias y foráneas.
    """
    # Conecta o crea la base de datos
    con = sqlite3.connect(db_filename)
    cur = con.cursor()

    # Borra las tablas si ya existen
    cur.execute("DROP TABLE IF EXISTS semanales_IBEX35")
    cur.execute("DROP TABLE IF EXISTS datos_generales")

    # Crea la tabla datos_generales
    cur.execute("""
        CREATE TABLE datos_generales (
            ticker TEXT PRIMARY KEY,
            nombre TEXT,
            indice TEXT,
            pais TEXT
        )
    """)

    # Crea la tabla semanales_IBEX35
    cur.execute("""
        CREATE TABLE semanales_IBEX35 (
            ticker TEXT,
            fecha TEXT,
            precio REAL,
            PRIMARY KEY (ticker, fecha),
            FOREIGN KEY (ticker) REFERENCES datos_generales(ticker)
        )
    """)

    con.commit()
    con.close()


def cargar_bd(db_filename, tab_datos, tab_ibex35):
    """
    Carga datos desde los ficheros CSV tab_datos y tab_ibex35 en la base de datos
    db_filename, transformando las fechas al formato YYYY-MM-DD HH:MM.
    """
    con = sqlite3.connect(db_filename)
    cur = con.cursor()

    # Cargar datos_generales
    with open(tab_datos, "r", encoding="utf-8") as f:
        lector = csv.DictReader(f, delimiter=';')
        for fila in lector:
            cur.execute("INSERT INTO datos_generales VALUES (?, ?, ?, ?)",
                        (fila["ticker"], fila["nombre"], fila["indice"], fila["pais"]))

    # Cargar semanales_IBEX35
    with open(tab_ibex35, "r", encoding="utf-8") as f:
        lector = csv.DictReader(f, delimiter=';')
        for fila in lector:
            # Cambiar formato de fecha de DD/MM/YYYY HH:MM a YYYY-MM-DD HH:MM
            fecha_original = fila["fecha"]
            fecha_nueva = datetime.strptime(fecha_original, "%d/%m/%Y %H:%M").strftime(
                "%Y-%m-%d %H:%M"
            )
            cur.execute("INSERT INTO semanales_IBEX35 VALUES (?, ?, ?)",
                        (fila["ticker"], fecha_nueva, float(fila["precio"])))

    con.commit()
    con.close()


def consulta1(db_filename, indice):
    """
    Devuelve una lista de tuplas (ticker, nombre) de acciones de un índice dado,
    ordenadas por ticker ascendente.
    """
    con = sqlite3.connect(db_filename)
    cur = con.cursor()

    cur.execute('''
        SELECT ticker, nombre
        FROM datos_generales
        WHERE indice LIKE ?
        ORDER BY ticker ASC
        ''', (indice,)
    )
    sol = cur.fetchall()
    con.close()
    return sol


def consulta2(db_filename):
    """
    Devuelve una lista de tuplas (ticker, nombre, precio_maximo) para cada valor
    del IBEX35 según la tabla histórica 'semanales_IBEX35', ordenada por nombre asc.
    """
    con = sqlite3.connect(db_filename)  #abrimos conexion a la BD
    cur = con.cursor() #obtenemos cursor para ejecutar sentencias SQL

    #construimos la consulta
    consulta = """
        SELECT dg.ticker, dg.nombre, MAX(s.precio) AS precio_maximo
        FROM datos_generales AS dg
        JOIN semanales_IBEX35 AS s
          ON s.ticker = dg.ticker
        GROUP BY dg.ticker, dg.nombre
        ORDER BY dg.nombre ASC
    """

    cur.execute(consulta) #ejecutamos la consulta
    resultado = cur.fetchall() #recuperamos todas las filas del resultado como lista de tuplas
    con.close() #cerramos conexión
    return resultado


def consulta3(db_filename, limite):
    """
    Devuelve una lista de tuplas (ticker, nombre, precio_promedio, diferencia_max_min)
    para las acciones del IBEX35 con precio promedio superior a limite, ordenada por
    precio promedio descendente.
    """
    con = sqlite3.connect(db_filename)  #abrimos conexion a la BD
    cur = con.cursor() #obtenemos cursor para ejecutar sentencias SQL

    #construimos la consulta
    consulta = """
        SELECT dg.ticker, dg.nombre, AVG(s.precio) AS precio_promedio,
               (MAX(s.precio) - MIN(s.precio)) AS diferencia_max_min
        FROM datos_generales AS dg
        JOIN semanales_IBEX35 AS s ON s.ticker = dg.ticker
        GROUP BY dg.ticker, dg.nombre
        HAVING AVG(s.precio) > ?
        ORDER BY precio_promedio DESC
    """

    cur.execute(consulta, (limite,)) #ejecutamos la consulta con el parametro limite
    resultado = cur.fetchall() #recuperamos todas las filas del resultado como lista de tuplas
    con.close() #cerramos conexión
    return resultado


def consulta4(db_filename, ticker):
    """
    Devuelve una lista de tuplas (ticker, fecha, precio) para las acciones del ticker
    indicado, ordenada por fecha de más reciente a más antiguo, mostrando solo el día.
    """
    con = sqlite3.connect(db_filename)  #abrimos conexion a la BD
    cur = con.cursor() #obtenemos cursor para ejecutar sentencias SQL

    #construimos la consulta usando date() para extraer solo el dia
    consulta = """
        SELECT ticker, date(fecha) AS fecha, precio
        FROM semanales_IBEX35
        WHERE ticker = ?
        ORDER BY fecha DESC
    """

    cur.execute(consulta, (ticker,)) #ejecutamos la consulta con el parametro ticker
    resultado = cur.fetchall() #recuperamos todas las filas del resultado como lista de tuplas
    con.close() #cerramos conexión
    return resultado
