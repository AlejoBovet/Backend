from django.db import models

class Alimento(models.Model):
    id_alimento = models.AutoField(primary_key=True)
    name_alimento = models.CharField(max_length=255)
    unit_measurement = models.CharField(max_length=255)
    load_alimento = models.IntegerField()

    def __str__(self):
        return self.name_alimento

class Dispensa(models.Model):
    id_dispensa = models.AutoField(primary_key=True)
    alimento = models.ForeignKey(Alimento, null=True, blank=True,on_delete=models.CASCADE)

    def __str__(self):
        return f"Dispensa {self.id_dispensa}"

class Users(models.Model):
    id_user = models.AutoField(primary_key=True)
    name_user = models.CharField(max_length=255)
    last_name_user = models.CharField(max_length=255)
    year_user = models.IntegerField()
    type_user = models.CharField(max_length=255)
    dispensa = models.OneToOneField(Dispensa, null=True, blank=True, on_delete=models.SET_NULL)

    def __str__(self):
        return f"{self.name_user} {self.last_name_user}"

class Minuta(models.Model):
    id_minuta = models.AutoField(primary_key=True)
    fecha = models.DateField(null=True, blank=True)
    type_food = models.CharField(max_length=255)
    name_food = models.CharField(max_length=255)
    state_minuta = models.BooleanField()
    user = models.ForeignKey(Users, on_delete=models.CASCADE)

    def __str__(self):
        return f"Minuta {self.id_minuta} - {self.name_food}"

class HistorialAlimentos(models.Model):
    id_historial = models.AutoField(primary_key=True)
    alimento = models.ForeignKey(Alimento, null=True, on_delete=models.SET_NULL)
    name_alimento = models.CharField(max_length=255)
    unit_measurement = models.CharField(max_length=255)
    load_alimento = models.IntegerField()
    dispensa = models.ForeignKey(Dispensa, null=True, on_delete=models.SET_NULL)
    user = models.ForeignKey(Users, on_delete=models.CASCADE)
    date_join = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Historial {self.id_historial} - {self.name_alimento}"