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
    
    #validar si hay una minuta activa
    try:
        state_minuta_user = ListaMinuta.objects.get(user=user, state_minuta=True)
    except ListaMinuta.DoesNotExist:
        print("No hay minuta activa para el usuario.")
        return {"status": "error", "message": "No hay minuta activa para el usuario."}

    # Obtener el ID de la minuta activa
    minuta_activa_id = state_minuta_user.id_lista_minuta
    print(f"ID de la minuta activa: {minuta_activa_id}")

    # recuperar minuta completa
    minuta_activa_total = ListaMinuta.objects.get(id_lista_minuta=minuta_activa_id)

    # recuperar cantidad de personas de la minuta activa
    cantidad_personas = InfoMinuta.objects.get(lista_minuta=minuta_activa_id).cantidad_personas
    
    # Obtener la minuta del día
     # Obtener las minutas del día
    minutas_del_dia = Minuta.objects.filter(lista_minuta=minuta_activa_id, fecha=date).all()

    if not minutas_del_dia:
        print(f"No hay comida registrada para la fecha {date} en la minuta activa.")
        return []

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
    print(f"Minuta del día: {minutas_list}")
    #guardar la minuta del dia en una lista ya que puede ser mas de una minuta
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
    
    
    #verificar alimenros recuerados
    #print("Alimentos usados en la minuta: ", alimentos_usados_list)

    # Validar el parámetro realizacion_minuta
    if str(realizacion_minuta).strip().lower() == "false":
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
                # Si la cantidad es 0 o menos, volver a enlazarlo a la despensa sin modificar load_alimento
                alimento_obj.load_alimento = alimento_obj.load_alimento
                alimento_obj.save()
                dispensa_alimento = DispensaAlimento(
                    alimento=alimento_obj,
                    dispensa=user.dispensa,
                )
                dispensa_alimento.save()
            else:
                # Si la cantidad es mayor a 0, restar y crear un nuevo alimento con la cantidad indicada por la IA
                alimento_obj.load_alimento = nueva_cantidad
                alimento_obj.save()
                nuevo_alimento = Alimento(
                    name_alimento=alimento["name_alimento"],
                    unit_measurement=alimento["unit_measurement"],
                    load_alimento=Decimal(alimento["load_alimento"]),
                    uso_alimento=alimento["uso_alimento"],
                )
                nuevo_alimento.save()
                dispensa_alimento = DispensaAlimento(
                    alimento=nuevo_alimento,
                    dispensa=user.dispensa,
                )
                dispensa_alimento.save()
 
        return {"status": "success", "message": "Producto/s repuesto/s a despensa", "analisis_reposicion": "analisis_reposicion"}

    # Retornar si la realizacion_minuta es diferente de false , se debe indicar bien hecho compliste la minuta
    return {"status": "success", "message": "Minuta completada correctamente, bien hecho."}


