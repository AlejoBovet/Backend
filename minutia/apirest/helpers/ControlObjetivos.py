from django.utils import timezone
from django.db import models
from ..models import Objetivo, ProgresoObjetivo

def control_objetivo_minuta(user_id, realizado):
    """
    Controla el progreso del objetivo de minuta para un usuario.

    Args:
        user_id (int): ID del usuario.
        realizado (bool): Indica si la minuta del día fue realizada.

    Returns:
        None
    """
    # Obtener el objetivo activo del usuario
    objetivo = Objetivo.objects.filter(user_id=user_id, completado=False).first()
    print(objetivo)

    # Verificar si existe un objetivo activo
    if objetivo is None:
        return None
    
    #verificar que el ofjetivo sea de tipo minutas completas
    if objetivo.id_tipo_objetivo.tipo_objetivo != 'minutas completas':
        return None

    # Si la minuta del día fue realizada
    if realizado == True:
        # Actualizar el progreso del objetivo
        progreso_acumulado_actual = objetivo.progresos.aggregate(total=models.Sum('progreso_diario'))['total'] or 0
        nuevo_progreso_acumulado = progreso_acumulado_actual + 1

        # Crear un nuevo registro de progreso
        nuevo_progreso = ProgresoObjetivo.objects.create(
            objetivo=objetivo,
            fecha=timezone.now().date(),
            progreso_diario=1,
            progreso_acumulado=nuevo_progreso_acumulado
        )

        # Verificar si el objetivo se ha completado
        if nuevo_progreso_acumulado >= objetivo.meta_total:
            objetivo.completado = True
            objetivo.save()
    else:
        # Si la minuta no fue realizada, no se hace nada
        return None


