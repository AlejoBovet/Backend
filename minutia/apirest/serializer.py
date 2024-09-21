from rest_framework import serializers
from .models import Users, Dispensa


# Users Serializer
class UsersSerializer(serializers.ModelSerializer):
    class Meta:
        model = Users
        fields = '__all__'

#Dispensa serializer
class DispensaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dispensa
        fields = '__all__'