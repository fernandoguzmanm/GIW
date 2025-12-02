"""
TODO: rellenar

Asignatura: GIW
Práctica 1
Grupo: XXXXXXX
Autores: Pablo Bernal Calleja

Declaramos que esta solución es fruto exclusivamente de nuestro trabajo personal. No hemos
sido ayudados por ninguna otra persona o sistema automático ni hemos obtenido la solución
de fuentes externas, y tampoco hemos compartido nuestra solución con otras personas
de manera directa o indirecta. Declaramos además que no hemos realizado de manera
deshonesta ninguna otra actividad que pueda mejorar nuestros resultados ni perjudicar los
resultados de los demás.
"""


# Ejercicio 1

def dimension(matriz):
    #si la matriz está vacía devuelve none
    if not matriz:
        return (None, None)
    #busca las filas de la matriz
    n_filas = len(matriz)
    #cogerá la fila con más elementos de la matriz que será el número de columnas
    n_columnas = max((len(fila) for fila in matriz))
    return (n_filas, n_columnas)



def es_cuadrada(matriz):
    #busca las filas de la matriz
    n_filas = len(matriz)
    #cogerá la fila con más elementos de la matriz que será el número de columnas
    n_columnas = max(len(fila) for fila in matriz)
    #return True if n_filas == n_columnas else False
    return n_filas == n_columnas


def es_simetrica(matriz):
    for i in matriz:
        for j in matriz:
            if matriz[i][j] != matriz [j][i]:
                return False
    return True



def multiplica_escalar(matriz, k):
    #se crea la matriz auxiliar para devolver
    matriz_aux = []
    #se recorren todos los elementos de la matriz de la llamada
    for fila in matriz:
        nueva_fila = []
        for x in fila:
            #multiplicamos el número por k y lo metemos en la fila
            nuevo_numero = x*k
            nueva_fila.append(nuevo_numero)
        #metemos la fila en la matriz auxiliar y repetimos hasta acabar con todas las filas
        matriz_aux.append(nueva_fila)
    return matriz_aux


#cambio el nombre de las variables para que no de fallo en pylint
def suma(m1, m2):
    matriz_resultado = []
    
    # iteramos sobre las filas de las matrices
    for fila1, fila2 in zip(m1, m2):
        nueva_fila = []
        
        # ahora iteramos sobre los elementos de las filas de ambas matrices conjuntamente
        for elemento1, elemento2 in zip(fila1, fila2):
            suma_elementos = elemento1 + elemento2
            #insertamos la suma en la fila de la matriz resultado
            nueva_fila.append(suma_elementos)
        #insertamos la fila en matriz resultado
        matriz_resultado.append(nueva_fila)
        
    return matriz_resultado



# Ejercicio 2
def validar(grafo):
    #si no encontramos las claves nodos o aristas el grafo no será válido
    if "nodos" not in grafo or "aristas" not in grafo: 
        return False

    #en nodos guardaremos un conjunto de los nodos para tener un acceso rápido
    nodos = set(grafo["nodos"])
    #en aristas guardaremos el diccionario de todas las aristas de cada vértice
    aristas = grafo["aristas"]
    
    #comprobamos si los el conjunto de nodos coincide con el conjunto de las claves de las aristas, de no coincidir devolvemos False
    nodos_aristas = set(aristas.keys())
    if nodos_aristas != nodos: 
        return False

    #ahora iteramos sobre los nodos de "aristas"
    for destinos in aristas.values():
        #e iteramos sobre las aristas de cada nodo
        for destino in destinos:
            #si para cada arista de un nodo va a un nodo inexistente en la lista de nodos no será válido
            if destino not in nodos: 
                return False

        #como en los conjuntos se eliminan los duplicados confirmamos que no hay aristas repetidas
        if len(destinos) != len(set(destinos)): 
            return False

    return True

def grado_entrada(grafo, nodo):
    #el grafo debe ser válido e incluir el nodo en él
    if not validar(grafo) or nodo not in grafo["nodos"]: 
        return -1 
    
    contador = 0 
    for destinos in grafo["aristas"].values(): 
        contador += destinos.count(nodo)
    return contador


def distancia(grafo, nodo):
    #el grafo debe ser válido e incluir el nodo en él
    if not validar(grafo) or nodo not in grafo["nodos"]:
        return None

    dist = {n: -1 for n in grafo["nodos"]}
    dist[nodo] = 0

    # lista de nodos que ya sabemos la distancia
    procesados = [nodo]
    #como se está actualizando la lista sobre la que vamos a iterar lo haremos sobre una copia de la misma usando [:]
    for actual in procesados[:]:
        for vecino in grafo["aristas"][actual]:
            if dist[vecino] == -1:
                dist[vecino] = dist[actual] + 1
                procesados.append(vecino)

    return dist



#a partir de aquí está el código para probar las funciones
matriz1 = [[1, 0, 2, 5], 
           [0, 3, 3, 5], 
           [1, 2, 2, 5]
        ]

matriz2 = [[1, 0, 1], 
           [0, 3, 2], 
           [1, 2, 2]
        ]

matriz3 = [[1, 0, 1], 
           [0, 3, 2], 
           [1, 2, 2]
        ]

print(dimension(matriz1))
print(dimension(matriz2))

print('es cuadrada' if es_cuadrada(matriz1) else 'no es cuadrada')

a = multiplica_escalar(matriz1, 10)

print(a)

b = suma(matriz2, matriz3)

print(b)

g = {"nodos": ["a", "b", "c", "d"],
  "aristas": {"a": ["a", "b", "c"],
            "b": ["a", "c"],
            "c": ["c"],
            "d": ["c"]
            }
    }


if (validar(g)):print("grafo ok ")
print(grado_entrada(g, "a"))
print(distancia(g, "a"))
