from datetime import datetime
from decimal import Decimal
from ..models import ListaMinuta, Minuta, Alimento, DispensaAlimento, InfoMinuta, MinutaIngrediente
from .procesoia import analizar_repocision_productos
from django.utils import timezone

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

    # Recuperar cantidad de personas de la minuta activa
    cantidad_personas = InfoMinuta.objects.get(lista_minuta=minuta_activa_id).cantidad_personas
    
    # Obtener las minutas del día
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
                "tipo_medida": ingrediente.tipo_medida,
                "cantidad": ingrediente.cantidad
            } for ingrediente in ingredientes
        ]
        minutas_list.append({
            "type_food": minuta.type_food,
            "name_food": minuta.name_food,
            "fecha": minuta.fecha,
            "ingredientes": ingredientes_list
        })
    
    # Obtener id de productos utilizados en la minuta
    try:
        alimentos_usados = InfoMinuta.objects.get(lista_minuta=minuta_activa_id).alimentos_usados_ids
    except InfoMinuta.DoesNotExist:
        print("No se encontró información de la minuta.")
        return {"status": "error", "message": "No se encontró información de la minuta."}

    print(f"Alimentos usados en la minuta: {alimentos_usados}")

    # Obtener los detalles de los alimentos usados
    alimentos_usados_list = []
    for alimento_id in alimentos_usados:
        try:
            alimento = Alimento.objects.get(id_alimento=alimento_id)
            alimentos_usados_list.append({
                "id_alimento": alimento.id_alimento,
                "name_alimento": alimento.name_alimento,
                "unit_measurement": alimento.unit_measurement,
                "load_alimento": alimento.load_alimento,
            })
        except Alimento.DoesNotExist:
            print(f"Alimento con ID {alimento_id} no encontrado.")
            continue

    if str(realizacion_minuta).strip().lower() == "true":
        # Iniciar proceso de IA para analizar qué productos reponer en la despensa
        analisis_reposicion = analizar_repocision_productos(minutas_list, alimentos_usados_list)
        print("Respuesta de la IA: ", analisis_reposicion)

        for alimento in analisis_reposicion:
            try:
                alimento_obj = Alimento.objects.get(id_alimento=int(alimento["id_alimento"]))
                # Convertir las unidades de medida si es necesario
                if alimento_obj.unit_measurement != alimento["unit_measurement"]:
                    if alimento_obj.unit_measurement == "kg" and alimento["unit_measurement"] == "gr":
                        alimento["load_alimento"] = Decimal(alimento["load_alimento"]) / 1000
                    elif alimento_obj.unit_measurement == "gr" and alimento["unit_measurement"] == "kg":
                        alimento["load_alimento"] = Decimal(alimento["load_alimento"]) * 1000
                    elif alimento_obj.unit_measurement == "lt" and alimento["unit_measurement"] == "ml":
                        alimento["load_alimento"] = Decimal(alimento["load_alimento"]) / 1000
                    elif alimento_obj.unit_measurement == "ml" and alimento["unit_measurement"] == "lt":
                        alimento["load_alimento"] = Decimal(alimento["load_alimento"]) * 1000
                    else:
                        print(f"Unidades de medida incompatibles para el alimento {alimento['name_alimento']}")
                        continue
            except Alimento.DoesNotExist:
                print(f"Alimento {alimento['name_alimento']} no encontrado, es posible que lo hayas utilizado todo en otro alimento,deberas regenerar la minuta.")
                continue
            nueva_cantidad = alimento_obj.load_alimento - Decimal(alimento["load_alimento"])
            
            if nueva_cantidad <= 0:
                # Si la cantidad es 0 o menos eliminar alimento de despensa y no crear uno nuevo
                alimento_obj.delete()
            else:
                # Si la cantidad es mayor a 0, restar cantidad y crear un nuevo alimento
                alimento_obj.load_alimento = nueva_cantidad
                alimento_obj.save()
        return {"status": "success", "message": "Minuta cumplida, se generó descuento de alimentos."}    

    else:
        return {"status": "success", "message": "No se realizó la minuta, no se genera descuento de alimentos."}   
    

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

# Función para editar la cantidad de un ingrediente en la minuta
def editar_cantidad_ingrediente_minuta(user, date, id_ingrediente, cantidad):
    """
    Edita la cantidad de un ingrediente en la minuta del día.

    Args:
        user (Users): El usuario cuya minuta activa se va a editar.
        date (datetime.date): La fecha para la cual se va a editar la comida.
        id_ingrediente (int): ID del ingrediente a editar.
        cantidad (str): Nueva cantidad del ingrediente.

    Returns:
        dict: Diccionario con detalles de la edición y el estado de la validación.
    """

    # Validar si hay una minuta activa
    try:
        state_minuta_user = ListaMinuta.objects.get(user=user, state_minuta=True)
    except ListaMinuta.DoesNotExist:
        #print("No hay minuta activa para el usuario.")
        return {"status": "error", "message": "No hay minuta activa para el usuario."}

    # Obtener el ID de la minuta activa
    minuta_activa_id = state_minuta_user.id_lista_minuta
    #print(f"ID de la minuta activa: {minuta_activa_id}")

    # Obtener la minuta del día
    try:
        minuta_dia = Minuta.objects.get(lista_minuta=minuta_activa_id, fecha=date)
    except Minuta.DoesNotExist:
        #print(f"No hay minuta registrada para la fecha {date} en la minuta activa.")
        return {"status": "error", "message": f"No hay minuta registrada para la fecha {date} en la minuta activa."}

    # Obtener el ingrediente a editar
    try:
        ingrediente = MinutaIngrediente.objects.get(id_minuta=minuta_dia, id_minuta_ingrediente=id_ingrediente)
    except MinutaIngrediente.DoesNotExist:
        #print(f"No se encontró el ingrediente con ID {id_ingrediente} en la minuta del día.")
        return {"status": "error", "message": f"No se encontró el ingrediente con ID {id_ingrediente} en la minuta del día."}
    
    # La cantidad debe ser menor o igual a la cantidad que se tiene en la despensa
    try:
        alimentos = Alimento.objects.filter(name_alimento=ingrediente.nombre_ingrediente, dispensaalimento__dispensa__users=user)
        if alimentos.exists():
            total_cantidad_despensa = sum(Decimal(alimento.load_alimento) for alimento in alimentos)
            if total_cantidad_despensa < Decimal(cantidad):
                #print(f"No hay suficiente cantidad de {ingrediente.nombre_ingrediente} en la despensa.")
                return {"status": "error", "message": f"No hay suficiente cantidad de {ingrediente.nombre_ingrediente} en la despensa."}
            
            if total_cantidad_despensa == Decimal(cantidad):
                # Si la cantidad es igual a la cantidad en la despensa, eliminar el alimento
                for alimento in alimentos:
                    alimento.delete()
                ingrediente.cantidad = cantidad
                ingrediente.save()
                return {"status": "success", "message": "recuerda que se eliminó el alimento de la despensa, puede que tengas que regenerar la minuta."}
        else:
            #print(f"No se encontró el alimento {ingrediente.nombre_ingrediente} en la base de datos.")
            return {"status": "error", "message": f"No se encontró el alimento {ingrediente.nombre_ingrediente} en la base de datos."}
    except Exception as e:
        #print(f"Error al verificar la cantidad del alimento en la despensa: {e}")
        return {"status": "error", "message": f"Error al verificar la cantidad del alimento en la despensa: {e}"}
    
    # Editar la cantidad del ingrediente
    try:
        ingrediente.cantidad = cantidad
        ingrediente.save()
    except Exception as e:
        #print(f"Error al editar la cantidad del ingrediente: {e}")
        return {"status": "error", "message": f"Error al editar la cantidad del ingrediente: {e}"}

    return {"status": "success", "message": "Cantidad del ingrediente editada correctamente."}



