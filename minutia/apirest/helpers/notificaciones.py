from apirest.models import ListaMinuta, DispensaAlimento, InfoMinuta

#funcion para verificar el estado de la minuta del usuario      
def verificar_estado_minuta(user_id):

    print(user_id)
    #verificar si existe minuta activa del usuario y generar mensaje de notificacion 
    minuta_activa = ListaMinuta.objects.filter(user=user_id, state_minuta=True).exists()

    if minuta_activa:
        return "Tienes una minuta activa. ¡Recuerda seguir tu plan alimenticio!"
    
    #verificar si existe minuta inactiva del usuario y generar mensaje de notificacion
    minuta_inactiva = ListaMinuta.objects.filter(user=user_id, state_minuta=False).exists()

    if minuta_inactiva:
        return "Aún no tienes una minuta creada. ¡Empieza creando una para organizar tu alimentación!"
    
    # si no hay notificaciones necesarias 
    return None
    

#funcion para verificar si hay alimentos en la dispensa
def verificar_dispensa(user_id, dispensa_id):
    # Verificar si la despensa del usuario tiene alimentos y generar mensaje de notificación
    alimentos_dispensa = DispensaAlimento.objects.filter(dispensa=dispensa_id).count()
    minuta_activa = ListaMinuta.objects.filter(user=user_id, state_minuta=True).exists()

    if alimentos_dispensa > 0:
        if minuta_activa == True:
            return None
        else:
            return "Tu despensa tiene alimentos. ¡Crea una minuta para planificar"
    else:
        return "Tu despensa está vacía. ¡Agrega alimentos para poder planificar tus comidas!"

    # Si no hay notificaciones necesarias 
    return None

# Función para verificar qué alimentos se utilizaron en la minuta
def verificar_alimentos_minuta(user_id):
    # Primero verificar si existe minuta activa del usuario
    minuta_activa = ListaMinuta.objects.filter(user=user_id, state_minuta=True).first()

    if not minuta_activa:
        print("No hay minuta activa para el usuario.")
        return None
    
    # Verificar los alimentos que se utilizaron en la minuta
    info_minuta = InfoMinuta.objects.filter(lista_minuta=minuta_activa).first()

    if not info_minuta:
        print("No hay información de minuta para la minuta activa.")
        return None
    
    alimentos_usados_ids = info_minuta.alimentos_usados_ids
    print(f"Alimentos usados en la minuta: {alimentos_usados_ids}")

    # Verificar si los alimentos que están en la despensa están en la minuta
    alimentos_dispensa = DispensaAlimento.objects.filter(dispensa=minuta_activa.user.dispensa).values_list('alimento_id', flat=True)
    print(f"Alimentos en la despensa: {list(alimentos_dispensa)}")

    alimentos_no_minuta = [alimento for alimento in alimentos_dispensa if alimento not in alimentos_usados_ids]
    print(f"Alimentos no en la despensa: {alimentos_no_minuta}")

    if alimentos_no_minuta:
        return f"En tu despensa hay alimentos que no se utilizaron en la minuta. ¡Recrea tu minuta!"
    else:
        return None
