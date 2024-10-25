from .models import ListaMinuta, DispensaAlimento

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