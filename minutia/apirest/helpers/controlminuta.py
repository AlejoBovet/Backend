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

def listproduct_minutafilter(product_list, type_food):
    """
    Filtra la lista de productos para devolver solo los que corresponden al tipo de comida.
    """
    # Crear una lista en mayúsculas para comparación
    type_food_upper = type_food.upper()

    # Filtrar la lista de productos debe tener al menos un uso de alimento que coincida con el tipo de comida
    filtered_list = [producto for producto in product_list if producto['uso_alimento'].upper() == type_food_upper]

    return filtered_list