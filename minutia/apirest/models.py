from django.db import models
from datetime import datetime

class Alimento(models.Model):
    id_alimento = models.AutoField(primary_key=True)
    name_alimento = models.CharField(max_length=255)
    unit_measurement = models.CharField(max_length=255)
    load_alimento = models.DecimalField(max_digits=10, decimal_places=1)
    uso_alimento = models.CharField(max_length=255, blank=True, null=True)
    fecha_ingreso = models.DateTimeField(default=datetime.now, blank=True)

    def __str__(self):
        return self.name_alimento

    def formatted_fecha_ingreso(self):
        return self.fecha_ingreso.strftime('%Y/%m/%d')

class DispensaAlimento(models.Model):
    dispensa = models.ForeignKey('Dispensa', on_delete=models.CASCADE)
    alimento = models.ForeignKey(Alimento, on_delete=models.CASCADE)

    class Meta:
        unique_together = (('dispensa', 'alimento'),)
        db_table = 'apirest_dispensa_alimentos'

class Dispensa(models.Model):
    id_dispensa = models.AutoField(primary_key=True)
    alimentos = models.ManyToManyField(Alimento, through=DispensaAlimento, blank=True)
    ultima_actualizacion = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Dispensa {self.id_dispensa}"
    
    def get_alimentos_details(self):
        return [
            {
                'id': alimento.id_alimento,
                'name': alimento.name_alimento,
                'unit': alimento.unit_measurement,
                'load': alimento.load_alimento,
                'uso_alimento': alimento.uso_alimento,
            }
            for alimento in self.alimentos.all()
        ]
    

USER_TYPE_CHOICES = [
    ('Estudiante', 'Estudiante'),
    ('Trabajador', 'Trabajador'),
    ('Ama de casa', 'Ama de casa'),
]

class Users(models.Model):
    id_user = models.AutoField(primary_key=True)
    name_user = models.CharField(max_length=255)
    last_name_user = models.CharField(max_length=255)
    year_user = models.IntegerField()
    user_type = models.CharField(max_length=50, choices=USER_TYPE_CHOICES)
    user_sex = models.CharField(max_length=50, choices=[('M', 'Masculino'), ('F', 'Femenino'), ('O', 'Otro')])
    date_join = models.DateTimeField(auto_now_add=True)
    dispensa = models.OneToOneField(Dispensa, null=True, blank=True, on_delete=models.SET_NULL)

    def __str__(self):
        return f"{self.name_user} {self.last_name_user}"



class ListaMinuta(models.Model):
    id_lista_minuta = models.AutoField(primary_key=True)
    user = models.ForeignKey(Users, related_name='listas_minuta', on_delete=models.CASCADE)
    nombre_lista_minuta = models.CharField(max_length=50)  # Nombre de la lista de minuta
    fecha_creacion = models.DateField(null=True, blank=True)  # Fecha de creación
    fecha_inicio = models.DateField(null=True, blank=True)  # Fecha de inicio
    fecha_termino = models.DateField(null=True, blank=True)  # Fecha de término
    state_minuta = models.CharField(max_length=50)  # Estado de la minuta

    def __str__(self):
        return f"ListaMinuta {self.id_lista_minuta} - {self.user.name_user} {self.user.last_name_user}"

TYPE_FOOD_CHOICES = [
    ('desayuno', 'Desayuno'),
    ('almuerzo', 'Almuerzo'),
    ('cena', 'Cena'),
]

class Minuta(models.Model):
    id_minuta = models.AutoField(primary_key=True)
    lista_minuta = models.ForeignKey(ListaMinuta, related_name='minutas', on_delete=models.CASCADE, null=True, blank=True)
    type_food = models.CharField(max_length=50, choices=TYPE_FOOD_CHOICES)  # Desayuno, Almuerzo, Cena
    name_food = models.CharField(max_length=255)  # Nombre del plato
    fecha = models.DateField(null=True, blank=True)  # Fecha de la minuta

    def __str__(self):
        return f"Minuta {self.id_minuta} - {self.name_food} ({self.type_food})"
    
class MinutaIngrediente(models.Model):
    id_minuta_ingrediente = models.AutoField(primary_key=True)
    id_minuta = models.ForeignKey(Minuta, on_delete=models.CASCADE, related_name='ingredientes')
    nombre_ingrediente = models.CharField(max_length=100)
    tipo_medida = models.CharField(max_length=50)
    cantidad = models.CharField(max_length=50)

class InfoMinuta(models.Model):
    id_info_minuta = models.AutoField(primary_key=True)
    lista_minuta = models.ForeignKey(ListaMinuta, related_name='info_minutas', on_delete=models.CASCADE)
    tipo_dieta = models.CharField(max_length=70)
    cantidad_personas = models.IntegerField()
    tipo_alimento = models.JSONField(blank=True,null=True)
    alimentos_usados_ids = models.JSONField(blank=True, default=list)
    estado_dias = models.JSONField(blank=True, default=list)
    contado_en_estadisticas = models.BooleanField(default=False)  # Nueva columna para el estado de los días

    def __str__(self):
        return f"InfoMinuta {self.id_info_minuta} - {self.tipo_dieta} ({self.cantidad_personas} personas)"

class HistorialAlimentos(models.Model):
    id_historial = models.AutoField(primary_key=True)
    name_alimento = models.CharField(max_length=255)
    unit_measurement = models.CharField(max_length=255)
    load_alimento = models.DecimalField(max_digits=10, decimal_places=1)
    user_id = models.IntegerField(null=True, blank=True)
    uso_alimento = models.CharField(max_length=255)
    dias_en_despensa = models.IntegerField(null=True)

    def __str__(self):
        return f"Historial {self.id_historial} - {self.name_alimento}"

class Sugerencias(models.Model):
    id_recomendacion = models.AutoField(primary_key=True)
    user = models.ForeignKey(Users, related_name='recomendaciones', on_delete=models.CASCADE)
    recomendacion = models.TextField()
    fecha = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"Recomendacion {self.id_recomendacion} - {self.user.name_user} {self.user.last_name_user}"

class Objetivo(models.Model):
    id_objetivo = models.AutoField(primary_key=True)
    user = models.ForeignKey(Users, related_name='objetivos', on_delete=models.CASCADE)
    id_tipo_objetivo = models.ForeignKey('TipoObjetivo', on_delete=models.CASCADE)
    meta_total = models.PositiveIntegerField()  # La cantidad total para cumplir el objetivo (ej. 10 minutas completas)
    completado = models.BooleanField(default=False)  
    state_objetivo = models.CharField(max_length=50)  # Estado del objetivo
    fecha_creacion = models.DateField(auto_now_add=True)
     
    def __str__(self):
        return f"{self.id_tipo_objetivo.tipo_objetivo} - {self.user}"
    
    
TIPO_OBJETIVO_CHOICES = [
    ('minutas completas', 'Minutas completas'),
    ('lista de minutas completas', 'Lista de minutas completas'),
    ('vegetales usados', 'Vegetales usados'),
    ('frutas usadas', 'Frutas usadas'),
    ('carbohidratos usados', 'Carbohidratos usados'),
]

class TipoObjetivo(models.Model):
    id_tipo_objetivo = models.AutoField(primary_key=True)
    tipo_objetivo = models.CharField(max_length=100, choices=TIPO_OBJETIVO_CHOICES) 
    

class ProgresoObjetivo(models.Model):
    objetivo = models.ForeignKey(Objetivo, related_name='progresos', on_delete=models.CASCADE)
    fecha = models.DateField(auto_now_add=True)   
    progreso_diario = models.PositiveIntegerField()   
    progreso_acumulado = models.PositiveIntegerField()   

    def __str__(self):
        return f"{self.objetivo.id_tipo_objetivo.tipo_objetivo} - {self.fecha}"
    
class Desperdicio(models.Model):
    id_desperdicio = models.AutoField(primary_key=True)
    user_id = models.IntegerField(null=True, blank=True)
    cantidad = models.FloatField()
    fecha = models.DateField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.alimento.name_alimento} - {self.cantidad}"
    

class EstadisticasUsuario(models.Model):
    usuario = models.OneToOneField(Users, related_name='estadisticas', on_delete=models.CASCADE)
    total_alimentos_ingresados = models.PositiveIntegerField(default=0)
    total_alimentos_eliminados = models.PositiveIntegerField(default=0)
    total_minutas_creadas = models.PositiveIntegerField(default=0)
    total_minutas_completadas = models.PositiveIntegerField(default=0)
    total_planes_creados = models.PositiveIntegerField(default=0)
    total_planes_completados = models.PositiveIntegerField(default=0)
    porcentaje_alimentos_aprovechados = models.FloatField(default=0.0)
    promedio_duracion_alimentos = models.FloatField(default=0.0)
    reduccion_desperdicio = models.FloatField(default=0.0)
    proporcion_planes_completados = models.FloatField(default=0.0)
    
    def __str__(self):
        return f"Estadísticas de {self.usuario}"