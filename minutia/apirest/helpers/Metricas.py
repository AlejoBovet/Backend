from collections import defaultdict
from datetime import datetime, date
from django.utils import timezone
from ..models import EstadisticasUsuario, HistorialAlimentos, InfoMinuta, ListaMinuta, Alimento, DispensaAlimento, Dispensa, Minuta, MinutaIngrediente, Users

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

# tiempo de alimento en la despensa
def tiempo_alimento_despensa(user, fecha_uso):
    """
    Calcula el tiempo promedio que un alimento permanece en la despensa antes de ser utilizado.

    Args:
        user_id (int): ID del usuario.
        fecha (datetime): Fecha actual.

    Returns:
        float: Tiempo promedio de permanencia de un alimento en la despensa.
    """
    # Convertir fecha_uso a datetime si es necesario
    if isinstance(fecha_uso, date):
        fecha_uso = datetime.combine(fecha_uso, datetime.min.time())

    # Asegurarse de que fecha_uso sea offset-naive
    if fecha_uso.tzinfo is not None and fecha_uso.utcoffset() is not None:
        fecha_uso = fecha_uso.replace(tzinfo=None)

    # Obtener la dispensa del usuario
    user_id = user.id_user
    try:
        dispensa_user = Users.objects.get(id_user=user_id).dispensa
    except Users.DoesNotExist:
        print(f"Usuario no encontrado con ID {user_id}")
        return 0

    # Obtener los id y fechas de los alimentos de la despensa
    alimentos_dispensa = DispensaAlimento.objects.filter(dispensa=dispensa_user)
    alimentos = []
    for alimento in alimentos_dispensa:
        # Asegurarse de que fecha_ingreso sea offset-naive
        fecha_ingreso = alimento.alimento.fecha_ingreso
        if fecha_ingreso.tzinfo is not None and fecha_ingreso.utcoffset() is not None:
            fecha_ingreso = fecha_ingreso.replace(tzinfo=None)
        alimentos.append({
            "id_alimento": alimento.alimento.id_alimento,
            "name_alimento": alimento.alimento.name_alimento,
            "fecha_ingreso": fecha_ingreso
        })

    # Obtener la minuta activa del usuario
    try:
        minuta_activa = ListaMinuta.objects.get(user_id=user_id, state_minuta=True)
    except ListaMinuta.DoesNotExist:
        print(f"No hay minuta activa para el usuario {user_id}")
        return 0

    # Obtener los alimentos de la minuta activa
    try:
        minuta_dia = Minuta.objects.get(lista_minuta=minuta_activa, fecha=fecha_uso)
    except Minuta.DoesNotExist:
        print(f"No hay minuta para la fecha {fecha_uso} para el usuario {user_id}")
        return 0

    # Obtener los alimentos usados en la minuta del día
    alimentos_usados = MinutaIngrediente.objects.filter(id_minuta=minuta_dia)
    alimentos_minuta = []
    for alimento in alimentos_usados:
        alimentos_minuta.append(alimento.nombre_ingrediente)

    # Obtener los alimentos que se usaron igualando nombre de alimento
    alimentos_usados_dispensa = []
    for alimento in alimentos_minuta:
        for alimento_dispensa in alimentos:
            if alimento == alimento_dispensa["name_alimento"]:
                alimentos_usados_dispensa.append(alimento_dispensa)

    # Obtener el tiempo de los alimentos en la despensa
    tiempo_alimento = []
    for alimento in alimentos_usados_dispensa:
        tiempo = (fecha_uso - alimento["fecha_ingreso"]).days
        tiempo_alimento.append({
            "id_alimento": alimento["id_alimento"],
            "name_alimento": alimento["name_alimento"],
            "tiempo": tiempo
        })

    # Guardar los días en la tabla de historial de alimentos según el ID que corresponda
    for alimento in tiempo_alimento:
        try:
            historial_alimento = HistorialAlimentos.objects.get(name_alimento=alimento["name_alimento"], user_id=user_id)
            if historial_alimento.dias_en_despensa is None:
                historial_alimento.dias_en_despensa = alimento["tiempo"]
                historial_alimento.save()
            else:
                # No sobreescribir
                pass
        except HistorialAlimentos.DoesNotExist:
            # Handle the case where the record does not exist
            print(f"HistorialAlimentos not found for {alimento['name_alimento']} and user {user_id}")
            continue

    return True
