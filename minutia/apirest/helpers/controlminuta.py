from datetime import datetime
from decimal import Decimal
from ..models import ListaMinuta, Minuta, Alimento, DispensaAlimento, InfoMinuta, MinutaIngrediente
from .procesoia import analizar_repocision_productos

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
    Obtiene y valida la minuta del día del usuario.

    Args:
        user (Users): El usuario cuya minuta activa se va a consultar.
        date (datetime.date): La fecha para la cual se va a obtener la comida.
        realizacion_minuta (str): Parámetro que indica si la minuta se realizó o no.

    Returns:
        dict: Diccionario con detalles de la minuta del día y el estado de la validación.
    """
    # Validar si hay una minuta activa
    try:
        state_minuta_user = ListaMinuta.objects.get(user=user, state_minuta=True)
    except ListaMinuta.DoesNotExist:
        print("No hay minuta activa para el usuario.")
        return {"status": "error", "message": "No hay minuta activa para el usuario."}

    # Obtener el ID de la minuta activa
    minuta_activa_id = state_minuta_user.id_lista_minuta
    print(f"ID de la minuta activa: {minuta_activa_id}")

    
    # Obtener la minuta del día
    minutas_del_dia = Minuta.objects.filter(lista_minuta=minuta_activa_id, fecha=date).all()

    if not minutas_del_dia:
        print(f"No hay comida registrada para la fecha {date} en la minuta activa.")
        return {"status": "error", "message": f"No hay comida registrada para la fecha {date} en la minuta activa."}

    print(f"Minuta del día: {minutas_del_dia}")

    # Guardar las minutas y sus ingredientes en una lista
    minutas_list = []
    for minuta in minutas_del_dia:
        ingredientes = MinutaIngrediente.objects.filter(id_minuta=minuta).all()
        ingredientes_list = [
            {
                "nombre": ingrediente.nombre_ingrediente,
                "cantidad": ingrediente.cantidad
            } for ingrediente in ingredientes
        ]
        minutas_list.append({
            "type_food": minuta.type_food,
            "name_food": minuta.name_food,
            "fecha": minuta.fecha,
            "ingredientes": ingredientes_list
        })
    
    # obtener id de productos utilizados en la minuta
    alimentos_usados = InfoMinuta.objects.get(lista_minuta=minuta_activa_id).alimentos_usados_ids
    print(f"Alimentos usados en la minuta: {alimentos_usados}")
    # Obtener los detalles de los alimentos usados
    alimentos_usados_list = []
    for alimento_id in alimentos_usados:
        alimento = Alimento.objects.get(id_alimento=alimento_id)
        alimentos_usados_list.append({
            "id_alimento": alimento.id_alimento,
            "name_alimento": alimento.name_alimento,
            "unit_measurement": alimento.unit_measurement,
            "load_alimento": alimento.load_alimento,
        })
    
    if str(realizacion_minuta).strip().lower() == "true":
        # Iniciar proceso de IA para analizar qué productos reponer en la despensa
        analisis_reposicion = analizar_repocision_productos(minutas_list, alimentos_usados_list)
        print("Respuesta de la IA: ", analisis_reposicion)

        for alimento in analisis_reposicion:
            try:
                alimento_obj = Alimento.objects.get(id_alimento=alimento["id_alimento"])
            except Alimento.DoesNotExist:
                print(f"Alimento {alimento['id_alimento']} no encontrado.")
                continue
            nueva_cantidad = alimento_obj.load_alimento - Decimal(alimento["load_alimento"])
            
            if nueva_cantidad <= 0:
                # Si la cantidad es 0 o menos eliminar alimento de despensa y no crear uno nuevo
                alimento_obj.delete()
            else:
                # Si la cantidad es mayor a 0, restar cantidad y crear un nuevo alimento
                alimento_obj.load_alimento = nueva_cantidad
                alimento_obj.save()

        print("La comida ha sido repuesta en la despensa.")
        return {"status": "success", "message": "Minuta completada correctamente, se han desconatdos los productos utlilizados.", "analisis_reposicion": analisis_reposicion}

    # Retornar si la realizacion_minuta es diferente de false , se debe indicar bien hecho compliste la minuta
    return {"status": "success", "message": "No se han descontado productos."}


#funcion para actualizar estado_dias en la tabla InfoMinuta
def update_estado_dias(user_id, date, realizacion_minuta):
    """
    Actualiza el estado de los días en la tabla InfoMinuta.

    Args:
        user_id (int): ID del usuario.
        date (datetime.date): Fecha para la cual se va a actualizar el estado.

    Returns:
        None
    """
    try:
        # Obtener la información de la minuta activa del usuario
        lista_minuta_activa = ListaMinuta.objects.filter(user_id=user_id, state_minuta=True).first()
        if not lista_minuta_activa:
            print("No hay minuta activa para el usuario.")
            return

        # Obtener el id de la minuta del día con la fecha actual
        minuta_dia = Minuta.objects.filter(lista_minuta=lista_minuta_activa, fecha=date).first()
        if not minuta_dia:
            print("No hay minuta para la fecha proporcionada.")
            return

        # Obtener la información de la minuta
        info_minuta = InfoMinuta.objects.filter(lista_minuta=lista_minuta_activa).first()
        if not info_minuta:
            print("No se encontró información de la minuta.")
            return

        # Obtener los estados de los días
        estados_dias = info_minuta.estado_dias or []

        # Filtrar por id de minuta
        estados_dias = [estado for estado in estados_dias if estado['id_minuta'] != minuta_dia.id_minuta]

        if str(realizacion_minuta).strip().lower() == "true":
            # Si la minuta se completó, actualizar el estado a 'c'
            # Actualizar key state correspondiente al id de la minuta
            estados_dias.append({
            "id_minuta": minuta_dia.id_minuta,
            "state": "c"
            })

            # Guardar los cambios en la base de datos
            info_minuta.estado_dias = estados_dias
            info_minuta.save()
        else:
            # Si la minuta no se completó, actualizar el estado a 'i'
            # Actualizar key state correspondiente al id de la minuta
            estados_dias.append({
            "id_minuta": minuta_dia.id_minuta,
            "state": "nc"
            })

            # Guardar los cambios en la base de datos
            info_minuta.estado_dias = estados_dias
            info_minuta.save()

    except Exception as e:
        print(f"Error al actualizar el estado de los días: {e}")

    return None