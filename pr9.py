"""
Gestión de la Información en la Web - Práctica 9
Asignatura: GIW
Práctica 9 - Autenticación & TOTP
Grupo: X
Autores: X

Declaramos que esta solución es fruto exclusivamente de nuestro trabajo personal. No hemos
sido ayudados por ninguna otra persona o sistema automático ni hemos obtenido la solución
de fuentes externas, y tampoco hemos compartido nuestra solución con otras personas
de manera directa o indirecta. Declaramos además que no hemos realizado de manera
deshonesta ninguna otra actividad que pueda mejorar nuestros resultados ni perjudicar los
resultados de los demás.
"""


from flask import Flask, request, render_template_string
from mongoengine import connect, Document, StringField, EmailField
import hashlib
import secrets
import base64
import pyotp
import qrcode
from io import BytesIO
import bcrypt


app = Flask(__name__)
connect('giw_auth')


# Clase para almacenar usuarios usando mongoengine
class User(Document):
    user_id = StringField(primary_key=True)
    full_name = StringField(min_length=2, max_length=50, required=True)
    country = StringField(min_length=2, max_length=50, required=True)
    email = EmailField(required=True)
    passwd = StringField(required=True)
    totp_secret = StringField(required=False)


##############
# APARTADO 1 #
##############

# 
# Mecanismo de almacenamiento de contraseñas:
# Utilizamos bcrypt para el hash seguro de contraseñas. Bcrypt es considerado
# uno de los métodos más seguros porque:
# 1. Usa salt automáticamente para prevenir ataques con tablas arcoíris
# 2. Es computacionalmente costoso, haciendo ataques por fuerza bruta muy lentos
# 3. Es resistente a ataques con GPU
# 4. El coste de trabajo es ajustable, permitiendo aumentar la seguridad con el tiempo
# 
# El proceso es:
# - Al crear/actualizar una contraseña: bcrypt.hashpw(password.encode(), bcrypt.gensalt())
# - Al verificar: bcrypt.checkpw(password.encode(), hashed_password)
# 
# Esto garantiza que incluso si la base de datos es comprometida, las contraseñas
# originales no pueden ser recuperadas fácilmente.
#

def hash_password(password):
    """Genera un hash seguro de la contraseña usando bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password, hashed):
    """Verifica si la contraseña coincide con el hash almacenado"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))


@app.route('/signup', methods=['POST'])
def signup():
    nickname = request.form.get('nickname')
    full_name = request.form.get('full_name')
    country = request.form.get('country')
    email = request.form.get('email')
    password = request.form.get('password')
    password2 = request.form.get('password2')
    
    # Verificar que las contraseñas coinciden
    if password != password2:
        return "Las contraseñas no coinciden"
    
    # Verificar si el usuario ya existe
    if User.objects(user_id=nickname).first():
        return "El usuario ya existe"
    
    # Crear nuevo usuario
    hashed_password = hash_password(password)
    user = User(
        user_id=nickname,
        full_name=full_name,
        country=country,
        email=email,
        passwd=hashed_password
    )
    user.save()
    
    return f"Bienvenido {full_name}"


@app.route('/change_password', methods=['POST'])
def change_password():
    nickname = request.form.get('nickname')
    old_password = request.form.get('old_password')
    new_password = request.form.get('new_password')
    
    # Buscar usuario
    user = User.objects(user_id=nickname).first()
    
    # Verificar usuario y contraseña antigua
    if not user or not verify_password(old_password, user.passwd):
        return "Usuario o contraseña incorrectos"
    
    # Actualizar contraseña
    user.passwd = hash_password(new_password)
    user.save()
    
    return f"La contraseña del usuario {nickname} ha sido modificada"


@app.route('/login', methods=['POST'])
def login():
    nickname = request.form.get('nickname')
    password = request.form.get('password')
    
    # Buscar usuario
    user = User.objects(user_id=nickname).first()
    
    # Verificar usuario y contraseña
    if not user or not verify_password(password, user.passwd):
        return "Usuario o contraseña incorrectos"
    
    return f"Bienvenido {user.full_name}"


##############
# APARTADO 2 #
##############

# 
# Generación de semilla aleatoria, URL de registro y código QR:
# 
# 1. Semilla aleatoria: Usamos secrets.token_bytes(20) para generar 20 bytes
#    aleatorios criptográficamente seguros, luego los codificamos en Base32.
#    secrets es más seguro que random para datos criptográficos.
# 
# 2. URL de registro: Usamos pyotp.TOTP(secret).provisioning_uri() que genera
#    una URL en el formato estándar otpauth://. Esta URL incluye:
#    - El secreto en Base32
#    - El nombre de usuario (nickname)
#    - El nombre del emisor (en nuestro caso "GIW_Auth")
# 
# 3. Código QR: Usamos la biblioteca qrcode para generar un código QR que
#    contiene la URL de registro. Luego convertimos la imagen a Base64 para
#    incrustarla directamente en el HTML usando data URLs.
# 
# Esto permite al usuario escanear el código QR con su app de autenticación
# y configurar automáticamente la cuenta TOTP.
#

def generate_totp_secret():
    """Genera un secreto TOTP aleatorio seguro"""
    return pyotp.random_base32()

def generate_qr_code(data):
    """Genera un código QR a partir de datos y lo devuelve como Base64"""
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(data)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    
    img_base64 = base64.b64encode(buffer.getvalue()).decode()
    return f"data:image/png;base64,{img_base64}"


@app.route('/signup_totp', methods=['POST'])
def signup_totp():
    nickname = request.form.get('nickname')
    full_name = request.form.get('full_name')
    country = request.form.get('country')
    email = request.form.get('email')
    password = request.form.get('password')
    password2 = request.form.get('password2')
    
    # Verificar que las contraseñas coinciden
    if password != password2:
        return "Las contraseñas no coinciden"
    
    # Verificar si el usuario ya existe
    if User.objects(user_id=nickname).first():
        return "El usuario ya existe"
    
    # Generar secreto TOTP
    totp_secret = generate_totp_secret()
    
    # Crear nuevo usuario con secreto TOTP
    hashed_password = hash_password(password)
    user = User(
        user_id=nickname,
        full_name=full_name,
        country=country,
        email=email,
        passwd=hashed_password,
        totp_secret=totp_secret
    )
    user.save()
    
    # Generar URL de registro
    totp = pyotp.TOTP(totp_secret)
    provisioning_url = totp.provisioning_uri(name=nickname, issuer_name="GIW_Auth")
    
    # Generar código QR
    qr_code = generate_qr_code(provisioning_url)
    
    # Plantilla HTML para mostrar el código QR
    html_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Registro TOTP Completado</title>
    </head>
    <body>
        <h1>Registro completado</h1>
        <p>Escanea el siguiente código QR con tu app de autenticación:</p>
        <img src="{{ qr_code }}" alt="Código QR TOTP">
        <p><strong>Usuario:</strong> {{ nickname }}</p>
        <p><strong>Secreto:</strong> {{ secret }}</p>
        <p>Si prefieres configurar manualmente, usa el secreto anterior.</p>
    </body>
    </html>
    """
    
    return render_template_string(html_template, 
                                qr_code=qr_code, 
                                nickname=nickname, 
                                secret=totp_secret)


@app.route('/login_totp', methods=['POST'])
def login_totp():
    nickname = request.form.get('nickname')
    password = request.form.get('password')
    totp_code = request.form.get('totp')
    
    # Buscar usuario
    user = User.objects(user_id=nickname).first()
    
    # Verificar usuario y contraseña
    if not user or not verify_password(password, user.passwd):
        return "Usuario o contraseña incorrectos"
    
    # Verificar código TOTP
    if not user.totp_secret:
        return "Usuario o contraseña incorrectos"
    
    totp = pyotp.TOTP(user.totp_secret)
    if not totp.verify(totp_code):
        return "Usuario o contraseña incorrectos"
    
    return f"Bienvenido {user.full_name}"


if __name__ == '__main__':
    app.config['ENV'] = 'development'
    app.config['DEBUG'] = True
    app.config['TESTING'] = True

    app.config['SECRET_KEY'] = 'giw_clave_secreta'

    app.config['STATIC_FOLDER'] = 'static'
    app.config['TEMPLATES_AUTO_RELOAD'] = True

    app.run(host='localhost', port=5000)
