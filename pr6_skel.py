"""
TODO: rellenar

Asignatura: GIW
Práctica 6
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

#para obtener la hora actual (función todos_no_cumplidos)
from datetime import datetime
import requests


BASE_URL = "https://gorest.co.in/public/v2"


def inserta_usuarios(datos, token):
    """
    Inserta todos los usuarios de la lista y devuelve el número de inserciones correctas.
    Si un usuario no se puede insertar (por ejemplo, email duplicado), se continúa con los demás.

    tanto aquí como en futuras ocasiones en la práctica, para cumplir con los requisitos de pylint
    y que las peticiones tipo requests no duren demasiado habrá que añadir a sus llamadas un 
    temporizador máximo
    """
    headers = {"Authorization": f"Bearer {token}"}
    correctos = 0

    for usuario in datos:
        try:
            r = requests.post(f"{BASE_URL}/users", headers=headers, json=usuario, timeout=5)
            if r.status_code == 201:
                correctos += 1
            # Si el error es por duplicado o cualquier otro, lo ignoramos y seguimos
        except requests.RequestException:
            continue  # Error de red o similar, ignoramos

    return correctos


def get_ident_email(email, token):
    """
    Devuelve el identificador del usuario cuyo email sea exactamente el pasado como parámetro.
    En caso de que ese usuario no exista devuelve None.
    """
    headers = {"Authorization": f"Bearer {token}"}
    params = {"email": email}
    try:
        r = requests.get(f"{BASE_URL}/users", headers=headers, params=params, timeout=5)
        if r.status_code != 200:
            return None

        usuarios = r.json()
        # La API devuelve coincidencias parciales, así que filtramos por igualdad exacta
        for u in usuarios:
            if u.get("email") == email:
                return u.get("id")
    except requests.RequestException:
        return None

    return None


def borra_usuario(email, token):
    """
    Elimina el usuario cuyo email sea exactamente el pasado como parámetro.
    En caso de éxito devuelve True. Si no existe tal usuario devolverá False.
    """
    user_id = get_ident_email(email, token)
    if user_id is None:
        return False

    headers = {"Authorization": f"Bearer {token}"}
    try:
        r = requests.delete(f"{BASE_URL}/users/{user_id}", headers=headers, timeout=5)
        return r.status_code == 204
    except requests.RequestException:
        return False

def inserta_todo(email, token, title, due_on, status='pending'):
    """ Inserta un nuevo ToDo para el usuario con email exactamente igual al pasado. 
        Si el ToDo ha sido insertado
        con éxito devolverá True, en otro caso devolverá False 
    """  
    #obtenemos el id del usuario
    user_id = get_ident_email(email, token)
    if user_id is None:
        return False
    #preparamos cabecera y datos para hacer la petición
    cabecera = {"Authorization": f"Bearer {token}"}
    todo_data = {
        "title": title,
        "due_on": due_on,
        "status": status
    }

    try:
        r = requests.post(f"{BASE_URL}/users/{user_id}/todos", headers=cabecera, json=todo_data, timeout=5)
        return r.status_code == 201
    except requests.RequestException:
        return False


def todos_usuario(email, token):

    """ Devuelve una lista de diccionarios con todos los ToDo asociados al usuario con el email pasado como
        parámetro """
    #obtenemos el id del usuario
    user_id = get_ident_email(email, token)
    if user_id is None:
        return []
    
    #preparamos cabecera
    cabecera = {"Authorization": f"Bearer {token}"}

    try:
        r = requests.get(f"{BASE_URL}/users/{user_id}/todos", headers=cabecera, timeout=5)
        if r.status_code != 200:
            return[]
        return r.json()
    except requests.RequestException:
        return []

    



def todos_no_cumplidos(email, token):
    """ Devuelve una lista de diccionarios con todos los ToDo asociados al usuario con el email pasado como
        parámetro que están pendientes (status=pending) y cuya fecha tope (due_on) es anterior a la fecha
        y hora actual. Para comparar las fechas solo hay que tener en cuenta el dia, la hora y los minutos; es
        decir, ignorar los segundos, microsegundos y el uso horario """
    
    #primero obtenemos las tareas del usuario usando la función creada anteriormente
    tareas = todos_usuario(email, token)
    if not tareas:
        return[]
    
    #obtenemos la fecha actual, sin tener en cuenta los segundos y microsegundos
    hora_actual = datetime.now().replace(second=0, microsecond=0)

    #creamos un contenedor donde iremos metiendo las tareas que cumplen los requisitos
    tareas_devueltas = []
    #recorremos todas las tareas viendo cuáles cumplen con los requisitos
    for t in tareas:
        
        if t.get("status") != "pending":
            continue

        hora_tarea = t.get("due_on")
        if not hora_tarea:
            continue

        #puede que la hora contenga zona horaria, la eliminamos
        hora_tarea = hora_tarea.split("+")[0].split("Z")[0]

        #intentamos cambiarlo de formato usando el datetime para igualarlo con nuestro formato de fecha actual
        try:
            hora_tarea =datetime.fromisoformat(hora_tarea).replace(second=0,microsecond=0)
        except ValueError:
            continue

        if hora_tarea < hora_actual:
            tareas_devueltas.append(t)

    return tareas_devueltas
