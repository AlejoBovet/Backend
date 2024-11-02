from datetime import datetime
from ..models import ListaMinuta, Minuta, Alimento, DispensaAlimento, InfoMinuta

# Cantidad de persona por alimentos
min_productos_por_personas = [
    (1, 4),  # 1 persona necesita un mínimo de 4 productos
    (2, 8),  # 2 personas necesitan un mínimo de 8 productos
    (3, 12), # 3 personas necesitan un mínimo de 12 productos
    (4, 16), # 4 personas necesitan un mínimo de 16 productos
    (5, 20), # 5 personas necesitan un mínimo de 20 productos
]

PRODUCTOS_DESAYUNO = [
    "SINGLES MILK", "CHOCOLATE ORLY", "GALL OREO SIXPAK", "BARRA 200G", "GALLETA CAPUC", "FRAC CLASICA", "GALL MOROCHA",
    "YOGURT", "CEREAL", "PAN INTEGRAL", "PAN DE MOLDE", "LECHE", "QUESO", "MERMELADA", "CAFÉ", "TÉ",
    "GALLETAS DE AVENA", "FRUTA FRESCA", "JUGO DE NARANJA", "CREMA DE CACAHUATE", "QUESO CREMA", "MUESLI", 
    "BARRITAS DE GRANOLA", "MIEL"
]
 
def minimoalimentospersona(alimentos_list, numero_personas):
    # Asegurar que numero_personas es un entero
    numero_personas = int(numero_personas)
    
    # Contar la lista de alimentos que tiene la persona
    cantidad_alimentos = len(alimentos_list)

    
    #print(f"Cantidad de alimentos: {cantidad_alimentos}")
    #print(f"Número de personas: {numero_personas}")

    # Buscar la cantidad mínima requerida para el número de personas
    for personas, min_productos in min_productos_por_personas:
        print(f"Verificando personas: {personas}, min_productos: {min_productos}")  # Debug
        if numero_personas == personas:
            if cantidad_alimentos < min_productos:
                print(f"Error: Debes tener al menos {min_productos} productos en tu despensa para {numero_personas} persona(s).")
                return f"Debes tener al menos {min_productos} productos en tu despensa para {numero_personas} persona(s)."
            break
    else:
        # Si no se encuentra el número de personas en la lista, devolver un error predeterminado
        print("Error: Número de personas no reconocido para establecer el mínimo de alimentos.")
        return "Número de personas no reconocido para establecer el mínimo de alimentos."

    return None

def alimentos_desayuno(lista_alimentos):
    """
    Recorre la lista de alimentos y reemplaza 'uso_alimento' con 'desayuno' 
    para los productos que deben ser usados solo en desayuno.
    """
    # Crear una lista en mayúsculas para comparación
    productos_desayuno_upper = [producto.upper() for producto in PRODUCTOS_DESAYUNO]

    for alimento in lista_alimentos:
        producto = alimento['producto'].strip().upper()
        if producto in productos_desayuno_upper:
            alimento['uso_alimento'] = 'desayuno'

    return lista_alimentos

def listproduct_minutafilter(alimentos_list, type_food):
    """
    Filtra los alimentos según el tipo o tipos de comida especificados.

    Args:
        alimentos_list (list): Lista de alimentos.
        type_food (str): Tipo(s) de comida, puede ser uno o varios separados por comas (ejemplo: 'desayuno,almuerzo').

    Returns:
        list: Lista filtrada de alimentos que corresponden a los tipos de comida especificados.
    """
    # Convertir type_food a una lista de tipos, eliminando espacios y convirtiendo a minúsculas
    type_food_list = [tipo.strip().lower() for tipo in type_food.split(',') if tipo.strip()]
    filtered_list = []

    for alimento in alimentos_list:
        # Obtener y procesar los usos del alimento
        uso_alimento = alimento.get('uso_alimento', '')
        usos_alimento_list = [uso.strip().lower() for uso in uso_alimento.split(',') if uso.strip()]
        
        # Verificar si hay intersección entre type_food_list y usos_alimento_list
        if set(type_food_list) & set(usos_alimento_list):
            filtered_list.append(alimento)
    
    return filtered_list

def obtener_y_validar_minuta_del_dia(user, date, realizacion_minuta):
    """
    Obtiene la comida del día de la minuta activa del usuario y valida el parámetro realizacion_minuta.
    Si realizacion_minuta es igual a "False", repone la comida que se había descontado para crear la minuta de ese día.

    Args:
        user (Users): El usuario cuya minuta activa se va a consultar.
        date (datetime.date): La fecha para la cual se va a obtener la comida.
        realizacion_minuta (str): Parámetro que indica si la minuta se realizó o no.

    Returns:
        dict: Diccionario con detalles de la minuta del día y el estado de la validación.
    """
    # Buscar la minuta activa del usuario
    minuta_activa = ListaMinuta.objects.filter(user=user, state_minuta=True).first()

    if not minuta_activa:
        print("No hay minuta activa para el usuario.")
        return {"status": "error", "message": "No hay minuta activa para el usuario."}

    # Traer comida del día de la minuta activa
    minuta_activa_dia = Minuta.objects.filter(lista_minuta=minuta_activa, fecha=date).first()

    if not minuta_activa_dia:
        print(f"No hay comida registrada para la fecha {date} en la minuta activa.")
        return {"status": "error", "message": f"No hay comida registrada para la fecha {date} en la minuta activa."}

    # Validar el parámetro realizacion_minuta
    if realizacion_minuta.lower() == "false":
        
        """ #recuperar la lista de id de alimentos usados en la minuta en alimentos_usados_ids
        lista_id_alimentos_usados = InfoMinuta.objects.filter(lista_minuta=minuta_activa).values('alimentos_usados_ids')

        #recuperar cantidad de personas de la minuta
        cantidad_personas = info_minuta.cantidad_personas

        # traer a una lista los alimentos desde la tabla alimentos con los id recuperados
        alimentos_usados = Alimento.objects.filter(id_alimento__in=info_minuta.alimentos_usados_ids).values('id_alimento', 'name_alimento')
        alimentos_usados_list = list(alimentos_usados)

        # crear lista de la minuta del dia 
        minuta_activa_dia = Minuta.objects.filter(lista_minuta=minuta_activa, fecha=date).first()

        #analizar -> enivar datos recuperados a la IA para analizar 
        #analisis = analizar_alimentos_usados(alimentos_usados_list, minuta_activa_dia, cantidad_personas)
        #print(f"Análisis de alimentos usados: {analisis}") """


        print("La comida ha sido repuesta en la despensa (comentado).")
        return {"status": "success", "message": "La comida ha sido repuesta en la despensa.", "minuta": minuta_activa_dia}

    return {"status": "success", "message": "Minuta del día obtenida y validada.", "minuta": minuta_activa_dia}