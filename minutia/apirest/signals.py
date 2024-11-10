from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import InfoMinuta, Objetivo, ProgresoObjetivo
from django.utils import timezone
from django.db import models

@receiver(post_save, sender=InfoMinuta)
def actualizar_objetivo_minutas(sender, instance, **kwargs):
    """
    Actualiza el progreso del objetivo de "minutas completas" cuando todos los estados son "completado".

    Args:
        sender (class): La clase del modelo que envía la señal.
        instance (InfoMinuta): La instancia del modelo que se ha guardado.
        **kwargs: Argumentos adicionales.
    """
    print("estoy activo")
    try:
        # Verificar que el usuario tenga un objetivo activo de tipo "lista de minutas completas"
        if not Objetivo.objects.filter(user=instance.lista_minuta.user, id_tipo_objetivo__tipo_objetivo='lista de minutas completas', completado=False).exists():
            return  # Sale si no es el tipo de objetivo correcto

        # Verificar si todos los estados son "completado"
        if all(estado.get('state') == 'c' for estado in instance.estado_dias):
            objetivo = Objetivo.objects.filter(
                user=instance.lista_minuta.user,
                id_tipo_objetivo__tipo_objetivo='lista de minutas completas',
                completado=False
            ).first()

            # Si existe un objetivo, actualizar el progreso
            if objetivo:
                # Crear un nuevo registro de progreso
                progreso = ProgresoObjetivo.objects.create(
                    objetivo=objetivo,
                    fecha=timezone.now().date(),
                    progreso_diario=1,
                    progreso_acumulado=objetivo.progresos.aggregate(total=models.Sum('progreso_diario'))['total'] + 1
                )

                # Completa el objetivo si se alcanzó la meta total
                if progreso.progreso_acumulado >= objetivo.meta_total:
                    objetivo.completado = True
                    objetivo.save()

    except Exception as e:
        print(f"Error al actualizar el objetivo de minutas completas: {e}")