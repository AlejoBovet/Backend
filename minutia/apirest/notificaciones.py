from .models import ListaMinuta


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
    

