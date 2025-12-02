"""
TODO: rellenar

Asignatura: GIW
Práctica 3
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

import xml.sax
from xml.etree import ElementTree as ET
from pathlib import Path
import html
from geopy.geocoders import Nominatim
from geopy.distance import geodesic

class ManejoRestaurantes(xml.sax.ContentHandler):
    """
    Creamos una clase contenthandler cuyo constructor tendrá 3 atributos, el texto para almacenar
    lo leído por invocaciones consecutivas, el en_name para saber si estamos en el atributo name y
    coger el nombre y un conjunto nombres donde iremos guardando los nombres de restaurantes
    """
    def __init__(self):
        super().__init__()
        self.texto = ""
        self.en_name = False
        self.nombres = set()

    def startElement(self, name, attrs):
        # cuando detecta la etiqueta element se pone en true nuestro en_name
        if name == "name":
            self.en_name = True
        # borramos lo que hubiese leído en el registro para coger solo el nombre
        self.texto = ""

    def characters(self, content):
        # cuando está leyendo el contenido de la etiqueta y nos encontramos en en_name,
        # y lo guardamos en el texto
        if self.en_name:
            self.texto += content

    def endElement(self, name):
        # cuando terminamos de ver un elemento si la etiqueta era name:
        if name == "name":
            # usamos el html.unescape() por el texto escapado html y el strip para
            # eliminar espacios al principio y al final
            nombre = html.unescape(self.texto.strip())
            # si existe el nombre lo añadimos a nuestro conjunto
            if nombre:
                self.nombres.add(nombre)
            # y como terminamos la etiqueta de name ponemos la flag a False
            self.en_name = False


def nombres_restaurantes(filename):
    """
    Devuelve una lista ordenada alfabéticamente con los nombres de los restaurantes
    del fichero XML especificado.
    """
    h = ManejoRestaurantes()
    parser = xml.sax.make_parser()
    parser.setContentHandler(h)
    parser.parse(filename)
    # usamos el método sorted para transformar el conjunto en una lista ordenada
    return sorted(h.nombres)


class SubcategoriaHandler(xml.sax.ContentHandler):
    """
    Clase para manejar la extracción de subcategorías del fichero XML.
    """
    def __init__(self):
        super().__init__()
        self.current_categoria = None
        self.current_subcategoria = None
        self.subcats = set()
        self.en_item = False
        self.attr_name = None
        self.buffer = ""

    def startElement(self, name, attrs):
        if name == "item":
            self.en_item = True
            self.attr_name = attrs.get("name")
            self.buffer = ""

    def characters(self, content):
        if self.en_item:
            self.buffer += content

    def endElement(self, name):
        if name == "item" and self.en_item:
            text = html.unescape(self.buffer.strip())
            if self.attr_name == "Categoria":
                self.current_categoria = text
            elif self.attr_name == "SubCategoria" and self.current_categoria:
                cadena = f"{self.current_categoria} > {text}"
                self.subcats.add(cadena)
            self.en_item = False
            self.attr_name = None
        elif name == "categoria":
            self.current_categoria = None


def subcategorias(filename):
    """
    Devuelve un conjunto con todas las subcategorías del XML en el formato 'Categoria > SubCategoria'.
    """
    handler = SubcategoriaHandler()
    parser = xml.sax.make_parser()
    parser.setContentHandler(handler)
    parser.parse(filename)
    return handler.subcats


def info_restaurante(filename, name):
    """
    Devuelve un diccionario con la información básica de un restaurante dado su nombre,
    o None si no se encuentra.
    """
    path = Path(filename).expanduser().resolve()
    tree = ET.parse(str(path))
    root = tree.getroot()

    # función limpiar
    def limpiar(txt):
        if txt is None:
            return None
        txt = txt.strip()
        return html.unescape(txt) if txt else None

    # buscar name
    for service in root.findall(".//service"):
        nombre_xml = service.findtext("basicData/name")
        if nombre_xml == name:
            # extraer campos básicos
            descripcion = service.findtext("basicData/body")
            email = service.findtext("basicData/email")
            web = service.findtext("basicData/web")
            phone = service.findtext("basicData/phone")

            # extraer el horario
            horario = None
            extra = service.find("extradata")
            if extra is not None:
                for it in extra.findall("item"):
                    candidato = limpiar(it.text)
                    if candidato:  # nos quedamos con el primero que no esté vacío
                        horario = candidato
                        break

            # montar y devolver el diccionario
            return {
                "nombre": limpiar(nombre_xml),
                "descripcion": limpiar(descripcion),
                "email": limpiar(email),
                "web": limpiar(web),
                "phone": limpiar(phone),
                "horario": limpiar(horario),
            }

    # si no se encontró ningún restaurante con ese nombre
    return None


def busqueda_cercania(filename, lugar, n):
    """
    Devuelve una lista de tuplas (distancia, nombre_restaurante) ordenada por distancia creciente
    con los restaurantes a <= n km del lugar indicado.
    """
    path = Path(filename).expanduser().resolve()
    tree = ET.parse(str(path))
    root = tree.getroot()

    # función limpiar
    def limpiar(txt):
        if txt is None:
            return None
        txt = txt.strip()
        return html.unescape(txt) if txt else None

    # geocodificar el lugar
    geolocator = Nominatim(user_agent="giw_practica")
    location = geolocator.geocode(lugar)
    if location is None:
        return []
    origin = (location.latitude, location.longitude)

    # buscar restaurantes y calcular distancias
    restaurantes = []
    for service in root.findall(".//service"):
        nombre_elem = service.find("basicData/name")
        if nombre_elem is None or nombre_elem.text is None:
            continue
        nombre = limpiar(nombre_elem.text)
        if not nombre:
            continue

        lat_elem = service.find("geoData/latitude")
        lon_elem = service.find("geoData/longitude")
        if lat_elem is None or lon_elem is None:
            continue

        try:
            lat = float(lat_elem.text)
            lon = float(lon_elem.text)
        except ValueError:
            continue

        dest = (lat, lon)
        dist = geodesic(origin, dest).km
        if dist <= n:
            restaurantes.append((dist, nombre))

    # ordenar por distancia
    return sorted(restaurantes)
