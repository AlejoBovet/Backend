from apirest.models import ListaMinuta, DispensaAlimento, InfoMinuta
from .sugerencias import analizar_despensa


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

    if alimentos_dispensa == 0 and minuta_activa:
        return "No hay alimentos en la despensa para la minuta, asegurate de tener lo necesario para cumplir con el plan."
    elif alimentos_dispensa > 0 and not minuta_activa:
        return "Tu despensa tiene alimentos. ¡Crea una minuta para organizar tu alimentación!"
    elif alimentos_dispensa == 0 and not minuta_activa:
        return "Tu despensa está vacía. ¡Agrega alimentos para poder planificar tus comidas!"
    else:
        return False
        

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
        #print("No hay información de minuta para la minuta activa.")
        return None
    
    alimentos_usados_ids = info_minuta.alimentos_usados_ids
    #print(f"Alimentos usados en la minuta: {alimentos_usados_ids}")

    # Verificar si los alimentos que están en la despensa están en la minuta
    alimentos_dispensa = DispensaAlimento.objects.filter(dispensa=minuta_activa.user.dispensa).values_list('alimento_id', flat=True)
    #print(f"Alimentos en la despensa: {list(alimentos_dispensa)}")

    alimentos_no_minuta = [alimento for alimento in alimentos_dispensa if alimento not in alimentos_usados_ids]
    #print(f"Alimentos no en la despensa: {alimentos_no_minuta}")

    if alimentos_no_minuta:
        return f"En tu despensa hay alimentos que no se utilizaron en la minuta. ¡Recrea tu minuta!"
    else:
        return None

def notificacion_sugerencia(user_id):
    mensaje_sugerencia = analizar_despensa(user_id)

    if mensaje_sugerencia == "Hay una recomendación para los productos que no utilizaste en tu minuta":
        return "¡Tienes sugerencias de uso para los alimentos en tu despensa!"
    elif mensaje_sugerencia == "No hay minuta activa para el usuario.":
        return "No hay minuta activa para el usuario."
    elif mensaje_sugerencia == "No hay alimentos en la despensa.":
        return "No hay alimentos en la despensa."
    else:
        return "No generar notificación"