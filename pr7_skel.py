"""
TODO: rellenar

Asignatura: GIW
Práctica X
Grupo: XXXXXXX
Autores: XXXXXX 

Declaramos que esta solución es fruto exclusivamente de nuestro trabajo personal. No hemos
sido ayudados por ninguna otra persona o sistema automático ni hemos obtenido la solución
de fuentes externas, y tampoco hemos compartido nuestra solución con otras personas
de manera directa o indirecta. Declaramos además que no hemos realizado de manera
deshonesta ninguna otra actividad que pueda mejorar nuestros resultados ni perjudicar los
resultados de los demás.
"""

from flask import Flask, request, session, render_template
app = Flask(__name__)

asignaturas = []
next_id = 0

def validar_asignatura(data):
    """Valida que la asignatura cumpla el esquema"""
    if not isinstance(data, dict):
        return False
    required = {"nombre": str, "numero_alumnos": int, "horario": list}
    for key, typ in required.items():
        if key not in data or not isinstance(data[key], typ):
            return False
    # Validar horario
    for h in data["horario"]:
        if not isinstance(h, dict):
            return False
        for campo in ["dia", "hora_inicio", "hora_final"]:
            if campo not in h:
                return False
        if not isinstance(h["dia"], str) or not isinstance(h["hora_inicio"], int) or not isinstance(h["hora_final"], int):
            return False
    return True


def validar_patch(data):
    """Valida un patch con un solo campo según el esquema"""
    if not isinstance(data, dict) or len(data) != 1:
        return False
    key, val = next(iter(data.items()))
    if key == "nombre" and isinstance(val, str):
        return True
    if key == "numero_alumnos" and isinstance(val, int):
        return True
    if key == "horario" and isinstance(val, list):
        for h in val:
            if not isinstance(h, dict):
                return False
            for campo in ["dia", "hora_inicio", "hora_final"]:
                if campo not in h:
                    return False
            if not isinstance(h["dia"], str) or not isinstance(h["hora_inicio"], int) or not isinstance(h["hora_final"], int):
                return False
        return True
    return False


@app.route("/asignaturas", methods=["GET", "POST", "DELETE"])
def manejador_asignaturas():
    global next_id
    if request.method == "DELETE":
        asignaturas.clear()
        return "", 204

    if request.method == "POST":
        data = request.get_json()
        if not validar_asignatura(data):
            return "", 400
        nueva = data.copy()
        nueva["id"] = next_id
        next_id += 1
        asignaturas.append(nueva)
        return jsonify({"id": nueva["id"]}), 201

    if request.method == "GET":
        # Filtrado y paginación
        try:
            page = request.args.get("page", type=int)
            per_page = request.args.get("per_page", type=int)
            alumnos_gte = request.args.get("alumnos_gte", type=int)
        except:
            return "", 400

        resultado = asignaturas
        if alumnos_gte is not None:
            resultado = [a for a in resultado if a["numero_alumnos"] >= alumnos_gte]

        # Paginación
        if (page is not None) != (per_page is not None):
            return "", 400
        if page and per_page:
            start = (page - 1) * per_page
            end = start + per_page
            pagina = resultado[start:end]
        else:
            pagina = resultado

        rutas = [f"/asignaturas/{a['id']}" for a in pagina]
        status = 200 if len(pagina) == len(resultado) else 206
        return jsonify({"asignaturas": rutas}), status


@app.route("/asignaturas/<int:aid>", methods=["GET", "PUT", "PATCH", "DELETE"])
def manejador_asignatura(aid):
    idx = next((i for i, a in enumerate(asignaturas) if a["id"] == aid), None)
    if request.method == "GET":
        if idx is None:
            return "", 404
        return jsonify(asignaturas[idx]), 200

    if request.method == "DELETE":
        if idx is None:
            return "", 404
        asignaturas.pop(idx)
        return "", 204

    data = request.get_json()
    if request.method == "PUT":
        if idx is None:
            return "", 404
        if not validar_asignatura(data):
            return "", 400
        nueva = data.copy()
        nueva["id"] = aid
        asignaturas[idx] = nueva
        return "", 200

    if request.method == "PATCH":
        if idx is None:
            return "", 404
        if not validar_patch(data):
            return "", 400
        asignaturas[idx].update(data)
        return "", 200


@app.route("/asignaturas/<int:aid>/horario", methods=["GET"])
def manejador_horario(aid):
    a = next((a for a in asignaturas if a["id"] == aid), None)
    if a is None:
        return "", 404
    return jsonify({"horario": a["horario"]}), 200

if __name__ == '__main__':
    # Activa depurador y recarga automáticamente
    app.config['ENV'] = 'development'
    app.config['DEBUG'] = True
    app.config['TEST'] = True

    # Imprescindible para usar sesiones
    app.config['SECRET_KEY'] = 'giw_clave_secreta'

    app.config['STATIC_FOLDER'] = 'static'
    app.config['TEMPLATES_FOLDER'] = 'templates'

    app.run()

