"""
TODO: rellenar

Asignatura: GIW
Práctica 8
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

from mongoengine import (
    Document,
    EmbeddedDocument,
    StringField,
    IntField,
    FloatField,
    ListField,
    EmbeddedDocumentListField,
    ReferenceField,
    ValidationError,
    signals,
    connect,
)

# Conectamos con los mismos parámetros que usan los tests
connect("giw_mongoengine", uuidRepresentation="standard")

"""
chuleta de comprobaciones con regex
    ^ -> inicio de la cadena
    \d -> un dígito
    {} -> repeticiones de un elemento
    $ -> final de cadena
"""


class Tarjeta(EmbeddedDocument):
    nombre = StringField(required=True, min_length=2)
    numero = StringField(required=True, regex=r"^\d{16}$")
    mes = StringField(required=True, regex=r"^\d{2}$")
    year = StringField(required=True, regex=r"^\d{2}$")
    cvv = StringField(required=True, regex=r"^\d{3}$")

    def clean(self):
        # nombre debe ser cadena
        if not isinstance(self.nombre, str):
            raise ValidationError("Nombre debe ser str")


def validar_dni(dni: str) -> bool:
    """Valida un DNI español clásico (8 dígitos + letra)"""
    letras = "TRWAGMYFPDXBNJZSQVHLCKE"
    if len(dni) != 9 or not dni[:8].isdigit() or not dni[-1].isalpha():
        return False
    numero = int(dni[:8])
    return dni[-1].upper() == letras[numero % 23]


class Producto(Document):
    codigo_barras = StringField(required=True, unique=True)
    nombre = StringField(required=True, min_length=2)
    categoria_principal = IntField(required=True, min_value=0)
    categorias_secundarias = ListField(IntField(min_value=0))

    def clean(self):
        # EAN debe ser una cadena
        if not isinstance(self.codigo_barras, str):
            raise ValidationError("EAN debe ser str")

        # Debe ser numérico y de 13 dígitos
        if len(self.codigo_barras) != 13 or not self.codigo_barras.isdigit():
            raise ValidationError("EAN debe ser un número de 13 dígitos")

        # Validar dígito de control EAN13
        nums = list(map(int, self.codigo_barras))
        suma_dig_imp = sum(
            nums[i] * (3 if i % 2 == 1 else 1) for i in range(12)
        )
        control = (10 - (suma_dig_imp % 10)) % 10
        if control != nums[12]:
            raise ValidationError("Dígito de control incorrecto")

        # Validar categorías
        if self.categorias_secundarias:
            if not isinstance(self.categorias_secundarias, list):
                raise ValidationError(
                    "Categorías secundarias debe ser una lista"
                )
            if self.categorias_secundarias[0] != self.categoria_principal:
                raise ValidationError(
                    "Categoría principal debe encontrarse en el primer lugar "
                    "de las categorías secundarias"
                )


class Linea(EmbeddedDocument):
    num_items = IntField(required=True, min_value=1)
    precio_item = FloatField(required=True, min_value=0)
    nombre_item = StringField(required=True, min_length=2)
    total = FloatField(required=True, min_value=0)
    producto = ReferenceField(Producto, required=True)

    def clean(self):
        # nombre_item debe ser cadena
        if not isinstance(self.nombre_item, str):
            raise ValidationError("nombre del item debe ser str")

        # total = num_items * precio_item (con pequeña tolerancia)
        if abs(self.total - (self.num_items * self.precio_item)) > 0.0001:
            raise ValidationError("total incorrecto")

        # nombre_item debe coincidir con producto.nombre
        if self.producto and self.nombre_item != self.producto.nombre:
            raise ValidationError(
                "nombre_item no coincide con producto.nombre"
            )


class Pedido(Document):
    total = FloatField(required=True, min_value=0)
    fecha = StringField(required=True)
    lineas = EmbeddedDocumentListField(Linea, required=True)

    def clean(self):
        # fecha debe ser str (los tests no piden validar formato)
        if not isinstance(self.fecha, str):
            raise ValidationError("fecha debe ser str")

        # lineas debe ser lista no vacía
        if not isinstance(self.lineas, list) or len(self.lineas) == 0:
            raise ValidationError("lineas debe ser una lista no vacía")

        # Validar cada línea (ejecuta su clean)
        for l in self.lineas:
            l.validate()

        # Comprobar que total sea la suma de los totales de las líneas
        suma = sum(l.total for l in self.lineas)
        if abs(self.total - suma) > 0.0001:
            raise ValidationError("total incorrecto")

        # Comprobar que no haya productos repetidos (usando el id)
        prods_ids = [str(l.producto.id) for l in self.lineas]
        if len(prods_ids) != len(set(prods_ids)):
            raise ValidationError("no puede haber productos repetidos")


class Usuario(Document):
    dni = StringField(required=True, unique=True)
    nombre = StringField(required=True, min_length=2)
    apellido1 = StringField(required=True, min_length=2)
    apellido2 = StringField()
    f_nac = StringField(required=True)  # se trabaja con string en los tests
    tarjetas = EmbeddedDocumentListField(Tarjeta)
    pedidos = ListField(ReferenceField("Pedido"))

    def clean(self):
        # DNI
        if not isinstance(self.dni, str) or not validar_dni(self.dni):
            raise ValidationError("DNI incorrecto")

        # Fecha de nacimiento, formato AAAA-MM-DD
        import datetime

        try:
            datetime.datetime.strptime(self.f_nac, "%Y-%m-%d")
        except ValueError as exc:
            raise ValidationError("Fecha incorrecta") from exc

        # Validar tarjetas
        if self.tarjetas:
            if not isinstance(self.tarjetas, list):
                raise ValidationError("tarjetas debe ser lista")
            for t in self.tarjetas:
                t.validate()

        # Validar pedidos
        if self.pedidos:
            if not isinstance(self.pedidos, list):
                raise ValidationError("pedidos debe ser lista")
            for p in self.pedidos:
                p.validate()


# Señal para eliminar referencias a pedidos en los usuarios
def borrar_pedido(sender, document, **kwargs):
    # document es el Pedido que se está borrando
    usuarios = Usuario.objects(pedidos=document)
    for u in usuarios:
        u.pedidos = [p for p in u.pedidos if p != document]
        u.save()


signals.pre_delete.connect(borrar_pedido, sender=Pedido)
