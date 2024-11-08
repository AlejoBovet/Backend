from collections import defaultdict
from ..models import HistorialAlimentos, InfoMinuta, ListaMinuta

def calcular_uso_frecuente_por_comida(user):
    """
    Calcula el uso frecuente de alimentos por tipo de comida para un usuario específico.

    Args:
        user_id (int): ID del usuario.

    Returns:
        list: Lista de diccionarios con el nombre del alimento y la frecuencia de uso por tipo de comida.
    """
    # Filtrar por id de usuario
    alimentos = HistorialAlimentos.objects.filter(user_id=user)

    # Inicializamos un diccionario para almacenar el conteo de cada comida para cada alimento
    uso_frecuente = defaultdict(lambda: {"desayuno": 0, "almuerzo": 0, "cena": 0})

    for alimento in alimentos:
        # Obtenemos el nombre del alimento
        nombre_alimento = alimento.name_alimento
        # Dividimos el campo 'uso_alimento' en una lista, separando por coma y espacio
        comidas = [comida.strip() for comida in alimento.uso_alimento.split(",")]

        # Contamos cada comida para el alimento
        for comida in comidas:
            if comida in uso_frecuente[nombre_alimento]:
                uso_frecuente[nombre_alimento][comida] += 1

    # Convertimos el diccionario a un formato más adecuado si es necesario
    resultado = []
    for nombre_alimento, conteos in uso_frecuente.items():
        resultado.append({
            "name_alimento": nombre_alimento,
            "frecuencia_uso": conteos
        })

    return resultado

def obtener_dieta_mas_usada(user_id):
    """
    Obtiene la dieta más usada por un usuario.

    Args:
        user_id (int): ID del usuario.

    Returns:
        str: Nombre de la dieta más usada.
    """
    # Filtrar por id de usuario a través de las relaciones
    minutas = InfoMinuta.objects.filter(lista_minuta__user=user_id)

    # Inicializamos un diccionario para almacenar el conteo de cada dieta
    conteo_dieta = defaultdict(int)

    for minuta in minutas:
        # Obtenemos el nombre de la dieta
        dieta = minuta.tipo_dieta

        # Contamos cada dieta
        conteo_dieta[dieta] += 1

    # Obtenemos la dieta más usada
    dieta_mas_usada = max(conteo_dieta, key=conteo_dieta.get)

    return dieta_mas_usada

def typo_food_mas_utlizado(user_id):
    """
    Obtiene el tipo de comida más utilizado en las minutas activas.

    Args:
        user_id (int): ID del usuario.

    Returns:
        str: Tipo de comida más utilizado.
    """
    # Filtrar por id de usuario a través de las relaciones
    minutas = InfoMinuta.objects.filter(lista_minuta__user=user_id)

    # Inicializamos un diccionario para almacenar el conteo de cada tipo de comida
    conteo_tipo_comida = defaultdict(int)

    for minuta in minutas:
        # Obtenemos el tipo de comida
        tipo_comida = minuta.tipo_alimento

        if tipo_comida:
            # Contamos cada tipo de comida
            for comida in tipo_comida.split(','):
                conteo_tipo_comida[comida.strip()] += 1

    # Obtenemos el tipo de comida más utilizado
    if conteo_tipo_comida:
        tipo_comida_mas_usado = max(conteo_tipo_comida, key=conteo_tipo_comida.get)
        print(f"Tipo de comida más utilizado: {tipo_comida_mas_usado}")
    else:
        tipo_comida_mas_usado = None

    return tipo_comida_mas_usado