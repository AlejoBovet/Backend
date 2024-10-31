# Cantidad de persona por alimentos
min_productos_por_personas = [
    (1, 4),  # 1 persona necesita un mínimo de 4 productos
    (2, 8),  # 2 personas necesitan un mínimo de 8 productos
    (3, 12), # 3 personas necesitan un mínimo de 12 productos
    (4, 16), # 4 personas necesitan un mínimo de 16 productos
    (5, 20), # 5 personas necesitan un mínimo de 20 productos
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



""" # Ejemplo de uso
alimentos_list = [
    {'id': 194, 'name': 'CAMARON', 'unit': 'kg', 'load': 1.0, 'uso': 'almuerzo, cena'},
    {'id': 195, 'name': 'CHORIZO RDA', 'unit': 'kg', 'load': 0.8, 'uso': 'almuerzo, cena'},
    {'id': 196, 'name': 'LONGANICILLA', 'unit': 'kg', 'load': 2.0, 'uso': 'almuerzo, cena'},
    {'id': 197, 'name': 'PECH DESH PO', 'unit': 'kg', 'load': 1.0, 'uso': 'almuerzo'},
    {'id': 198, 'name': 'ENTRANA CERD', 'unit': 'kg', 'load': 1.2, 'uso': 'almuerzo'},
    {'id': 199, 'name': 'COST CERDO', 'unit': 'kg', 'load': 3.0, 'uso': 'almuerzo'},
    {'id': 200, 'name': 'LONGANIZA 50', 'unit': 'kg', 'load': 0.9, 'uso': 'almuerzo'}
]
numero_personas = 3
print("Verificando mínimos de alimentos por persona...")
resultado = minimoalimentospersona(alimentos_list, numero_personas)
if resultado:
    print(resultado)
else:
    print("Se cumplen los mínimos de alimentos.") """