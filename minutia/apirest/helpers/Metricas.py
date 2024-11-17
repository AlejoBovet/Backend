from collections import defaultdict
from ..models import EstadisticasUsuario, HistorialAlimentos, InfoMinuta, ListaMinuta

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

    ## controlar minimos de alimentos para una mejor recomendacion
    # trar cantidad historica de alimentos del usuario
    cantidad_alimentos = len(alimentos)
    if cantidad_alimentos < 30:
        return None

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

def data_minima_recomendacion_compra(user, type_recomendacion):
    """
    Controla la data mínima para realizar una recomendación de compra.

    Args:
        user (User): Usuario para el cual se realiza la recomendación.
        type_recomendacion (int): Tipo de recomendación.

    Returns:
        str: "pass" si cumple con los mínimos, en caso contrario "error" para responder que no hay recomendación para el usuario.
    """
    user_id = user.id_user  # Obtener el ID del usuario

    if type_recomendacion == 1:
        # Traer cantidad histórica de alimentos del usuario
        cantidad_alimentos = HistorialAlimentos.objects.filter(user_id=user_id).count()
        print(f"Cantidad de alimentos: {cantidad_alimentos}")
        if cantidad_alimentos < 30:
            return "error"
        return "pass"
    elif type_recomendacion == 2:
        # Traer cantidad de minutas creadas por el usuario
        cantidad_minutas = ListaMinuta.objects.filter(user=user).count()
        if cantidad_minutas < 5:
            return "error"
        return "pass"
    elif type_recomendacion == 3:
        cantidad_alimentos = HistorialAlimentos.objects.filter(user_id=user_id).count()
        cantidad_minutas = ListaMinuta.objects.filter(user=user).count()
        if cantidad_alimentos < 30 or cantidad_minutas < 3:
            return "error"
        return "pass"
    return "pass"

## Metricas para estadisticas del usuario
# Porcentaje de alimentos aprovechados
def porcentaje_alimentos_aprovechados(user_id):
    """
    Muestra qué porcentaje de los alimentos ingresados han sido utilizados en planes completados.

    Args:
        user_id (int): ID del usuario.

    Returns:
        float: Porcentaje de alimentos aprovechados.
    """
    # Filtrar por id de usuario
    total_alimentos = EstadisticasUsuario.objects.filter(user_id=user_id).first().total_alimentos_ingresados

    # obtener la cantidad de alimentos usados en planes completados
    # Recuperar los planes completados
    planes_completados = InfoMinuta.objects.filter(lista_minuta__user=user_id, lista_minuta__state_minuta=False)
    # Contar los alimentos usados en los planes completados
    total_alimentos_usados = sum(len(plan.alimentos_usados_ids) for plan in planes_completados)
    
    porcentaje = (total_alimentos_usados / total_alimentos) * 100
    
    return porcentaje


