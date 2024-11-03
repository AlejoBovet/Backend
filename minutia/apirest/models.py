from django.db import models

class Alimento(models.Model):
    id_alimento = models.AutoField(primary_key=True)
    name_alimento = models.CharField(max_length=255)
    unit_measurement = models.CharField(max_length=255)
    load_alimento = models.DecimalField(max_digits=10, decimal_places=1)
    uso_alimento = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.name_alimento

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
    cantidad = models.CharField(max_length=50)

class InfoMinuta(models.Model):
    id_info_minuta = models.AutoField(primary_key=True)
    lista_minuta = models.ForeignKey(ListaMinuta, related_name='info_minutas', on_delete=models.CASCADE)
    tipo_dieta = models.CharField(max_length=70)
    cantidad_personas = models.IntegerField()
    alimentos_usados_ids = models.JSONField(blank=True, default=list)

    def __str__(self):
        return f"InfoMinuta {self.id_info_minuta} - {self.tipo_dieta} ({self.cantidad_personas} personas)"

class HistorialAlimentos(models.Model):
    id_historial = models.AutoField(primary_key=True)
    alimento_id = models.IntegerField(null=True, blank=True)  # Reemplaza la ForeignKey por un IntegerField
    name_alimento = models.CharField(max_length=255)
    unit_measurement = models.CharField(max_length=255)
    load_alimento = models.IntegerField()
    dispensa_id = models.IntegerField(null=True, blank=True)  # Reemplaza la ForeignKey por un IntegerField
    user_id = models.IntegerField(null=True, blank=True)  # Reemplaza la ForeignKey por un IntegerField
    date_join = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Historial {self.id_historial} - {self.name_alimento}"

class Sugerencias(models.Model):
    id_recomendacion = models.AutoField(primary_key=True)
    user = models.ForeignKey(Users, related_name='recomendaciones', on_delete=models.CASCADE)
    recomendacion = models.TextField()
    fecha = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"Recomendacion {self.id_recomendacion} - {self.user.name_user} {self.user.last_name_user}"

""" class Objetivos (models.Model):
    id_objetivo = models.AutoField(primary_key=True)
    user = models.ForeignKey(Users, related_name='objetivos', on_delete=models.CASCADE)
    objetivo = models.TextField()
    fecha = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"Objetivo {self.id_objetivo} - {self.user.name_user} {self.user.last_name_user}" """