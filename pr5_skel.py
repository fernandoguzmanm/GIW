"""
TODO: rellenar

Asignatura: GIW
Práctica 5
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

import re
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup

URL = 'https://books.toscrape.com/'


# APARTADO 1 #
def explora_categoria(url):
    """
    Devuelve una tupla (nombre, número de libros) explorando la URL de una categoría.
    """
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        # Obtener el nombre de la categoría desde el título de la página
        title = soup.find('h1').text.strip()
        
        # Obtener el número total de libros (si está disponible en el texto)
        article = soup.find('article', class_='product_pod')
        if article:
            pagination = soup.select_one('form .form-horizontal + ul.pager li.current')
            if pagination:
                text = pagination.text.strip()
                match = re.search(r'of (\d+)', text)
                if match:
                    total_pages = int(match.group(1))
                    num_books = total_pages * 20  # Asumiendo 20 libros por página
                else:
                    num_books = 20  # Si no hay paginación, asumimos 20 libros
            else:
                num_books = 20  # Valor por defecto si no hay paginación
        else:
            num_books = 0  # Si no hay productos, 0 libros
        
        return (title, num_books)
    except requests.RequestException:
        return ("Error", 0)


def categorias():
    """
    Devuelve un conjunto de parejas (nombre, número libros) de todas las categorías.
    """
    try:
        response = requests.get(URL, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Encontrar la lista de categorías en la barra lateral
        sidebar = soup.find('div', class_='side_categories')
        categories = set()
        
        if sidebar:
            # Extraer enlaces de categorías
            for a in sidebar.find_all('a', href=True):
                category_url = urljoin(URL, a['href'])
                name, num_books = explora_categoria(category_url)
                categories.add((name, num_books))
        
        return categories
    except requests.RequestException:
        return set()




# APARTADO 2 #

def url_categoria(nombre):
    """
    devuelve la URL de la página principal de una categoría a partir de su
    nombre. Para esta búsqueda debéis ignorar espacios al principio y final y también diferencias en
    mayúsculas/minúsculas.
    """
    try:

        #primero vamos a la página principal
        response = requests.get(URL, timeout=10) #descargamos la página
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        #normalizamos la entrada
        nombre_normalizado = nombre.strip().lower()

        #buscamos el contenedor lateral de categorías
        sidebar = soup.find('div', class_='side_categories')
        #si no se encuentra en las categorías salimos
        if not sidebar:
            return None
        
        #recorremos los enlaces dentro de la lista de categorías
        for a in sidebar.find_all('a', href=True):
            categoria_nombre = a.get_text(strip=True).lower()
            if categoria_nombre == nombre_normalizado:
                #convertimios la URL relativa en absoluta juntando la url principal
                #a la url de la categoría concreta
                categoria_url = urljoin(URL, a['href'])
                return categoria_url

        #si no se encuentra la categoría se devuelve none
        return None
    
    except requests.RequestException:
        return None

def todas_las_paginas(url):
    """
    a partir de la URL de una página, sigue la paginación hacia delante devolviendo una lista con todas 
    las URL absolutas atravesadas (incluyendo la URL inicial)
    """
    paginas = [url]
    try:
        actual = url
        while True:
            #descargamos la página en la que nos encontramos
            response = requests.get(actual, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')

            #buscamos el enlace a la siguiente página sabiendo cómo se indican las páginas en Books to Scrape
            next_link = soup.select_one('li.next a')
            #si no existe el siguiente link estamos en el final
            if not next_link:
                break

            #construimos la url absoluta de la siguiente página
            sig = urljoin(actual, next_link['href'])
            paginas.append(sig)

            actual = sig

        return paginas
    except requests.RequestException:
        return paginas #devuelve lo recorrido hasta el error

def libros_categoria(nombre):
    """ Dado el nombre de una categoría, devuelve un conjunto de tuplas 
        (titulo, precio, valoracion), donde el precio será un número real y la 
        valoración un número natural """
    #primero obtenemos el url de la categoría, si no existe devolveremos un conjunto vacío
    url = url_categoria(nombre)
    if not url:
        return set()
    
    #si existe obtenemos todas las páginas de la categoría
    paginas = todas_las_paginas(url)

    libros = set()
    valoraciones = {"One":1, "Two":2, "Three":3, "Four":4, "Five":5}

    #recorremos todas las páginas de la categoría
    for pagina in paginas:
        try:
            response = requests.get(pagina, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')

            #buscamos todos los artículos de libros
            articulos = soup.find_all('article', class_='product_pod')

            for articulo in articulos:
                #primero cogemos el título
                titulo = articulo.h3.a['title'].strip()

                #ahora el precio
                precio_txt = articulo.find('p', class_='price_color').text
                precio = float(precio_txt.replace('£', '').strip()) #para eliminar las unidades y dejar solo el número

                #ahora la valoración que está en el enlace css
                p_rating = articulo.find('p', class_='star-rating')
                for clase in p_rating['class']:
                    if clase in valoraciones:
                        valoracion = valoraciones[clase]
                        break
                else:
                    valoracion = 0

                libros.add((titulo, precio, valoracion))

        except requests.RequestException:
            continue

    return libros



#prueba explora_categoria
url_fiction = "https://books.toscrape.com/catalogue/category/books/historical-fiction_4/index.html"
print(explora_categoria(url_fiction))

#prueba categorias
cats = categorias()
print(len(cats), "categorías encontradas")
for c in sorted(list(cats))[:5]: #muestra solo 5
    print(c)

#prueba url_categoria
print(url_categoria('Historical Fiction'))
print(url_categoria('HISTORICAL FICTION'))

#prueba todas_las_paginas
url_misterio = url_categoria('Mystery')
print(todas_las_paginas(url_misterio))

#prueba libros_categoria
libros = libros_categoria('historical fiction')
print("Numero de libros: ", len(libros))
for lib in list(libros)[:5]:
    print(lib)
