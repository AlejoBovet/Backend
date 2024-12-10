from rest_framework import serializers
from .models import Users, Dispensa, Alimento,DispensaAlimento, Objetivo, ProgresoObjetivo


# Users Serializer
class UsersSerializer(serializers.ModelSerializer):
    class Meta:
        model = Users
        fields = '__all__'

#Alimento serializer
class AlimentoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Alimento
        fields = '__all__'

# DispensaAlimento Serializer
class DispensaAlimentoSerializer(serializers.ModelSerializer):
    alimento = AlimentoSerializer()

    class Meta:
        model = DispensaAlimento
        fields = ['alimento']

class DispensaSerializer(serializers.ModelSerializer):
    alimentos = serializers.SerializerMethodField()

    class Meta:
        model = Dispensa
        fields = '__all__'

    def get_alimentos(self, obj):
        dispensa_alimentos = DispensaAlimento.objects.filter(dispensa=obj)
        return DispensaAlimentoSerializer(dispensa_alimentos, many=True).data
    
class ObjetivoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Objetivo
        fields = '__all__'

class ProgresoObjetivoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProgresoObjetivo
        fields = '__all__'