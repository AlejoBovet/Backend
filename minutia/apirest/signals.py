from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import DispensaAlimento, HistorialAlimentos, InfoMinuta, ListaMinuta, Objetivo, ProgresoObjetivo, Alimento, Minuta,  EstadisticasUsuario
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
    #print("estoy activo")
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

# Signal para actualizar estadísticas al agregar un alimento
@receiver(post_save, sender=DispensaAlimento)
def actualizar_alimentos_ingresados(sender, instance, created, **kwargs):
    if created:  # Si se agregó un nuevo alimento a la dispensa
        try:
            usuario = instance.dispensa.users  # Obtener el usuario a través de la relación dispensa
            if usuario:
                estadisticas, _ = EstadisticasUsuario.objects.get_or_create(usuario=usuario)
                estadisticas.total_alimentos_ingresados += 1
                estadisticas.save()
        except Exception as e:
            print(f"Error al actualizar el historial de alimentos ingresados: {e}")


# Signal para actualizar estadísticas plan completado
@receiver(post_save, sender=InfoMinuta)
def actualizar_planes_creados(sender, instance, **kwargs):
    if all(estado.get('state') == 'c' for estado in instance.estado_dias):
        try:
            estadisticas, _ = EstadisticasUsuario.objects.get_or_create(usuario=instance.lista_minuta.user)
            estadisticas.total_planes_completados += 1
            estadisticas.save()
        except Exception as e:
            print(f"Error al actualizar las estadísticas de planes completados: {e}")


# Signal para actualizar estadísticas  Porcentaje de Alimentos Aprovechados
# Indica la eficiencia en el uso de los alimentos y si se está reduciendo el desperdicio.
@receiver(post_save, sender=InfoMinuta)
def actualizar_porcentaje_alimentos_aprovechados(sender, instance, **kwargs):
    if all(estado.get('state') == 'c' for estado in instance.estado_dias):
        try:
            usuario = instance.lista_minuta.user
            estadisticas, _ = EstadisticasUsuario.objects.get_or_create(usuario=usuario)
            total_alimentos = estadisticas.total_alimentos_ingresados
            print(f"Total alimentos: {total_alimentos}")
            total_alimentos_usados = sum(len(plan.alimentos_usados_ids) for plan in InfoMinuta.objects.filter(lista_minuta__user=usuario, lista_minuta__state_minuta=False))
            print(f"Total alimentos usados: {total_alimentos_usados}")
            porcentaje = (total_alimentos_usados / total_alimentos) * 100
            estadisticas.porcentaje_alimentos_aprovechados = porcentaje
            estadisticas.save()
        except Exception as e:
            print(f"Error al actualizar el porcentaje de alimentos aprovechados: {e}")

# Signal para actualizar estadísticas al crear una minuta
@receiver(post_save, sender=Minuta)
def actualizar_minutas_creadas(sender, instance, created, **kwargs):
    if created:  # Si se creó una nueva minuta
        try:
            usuario = instance.lista_minuta.user  # Obtener el usuario a través de la relación lista_minuta
            if usuario:
                estadisticas, _ = EstadisticasUsuario.objects.get_or_create(usuario=usuario)
                estadisticas.total_minutas_creadas = Minuta.objects.filter(lista_minuta__user=usuario).count()
                estadisticas.save()
        except Exception as e:
            print(f"Error al actualizar el historial de minutas creadas: {e}")

# Signal para promediar la duración de productos en la despensa
