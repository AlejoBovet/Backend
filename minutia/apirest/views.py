from rest_framework import viewsets
from rest_framework.decorators import api_view, schema
from rest_framework.response import Response
from rest_framework.schemas import AutoSchema
from .models import Users,Dispensa,Alimento,DispensaAlimento
from .serializer import UsersSerializer,DispensaSerializer
import coreapi
import coreschema
import tempfile



# Prueba de documentacion



# Create your views for the API here.

#register User
@api_view(['POST'])
@schema(AutoSchema(
    manual_fields=[
        coreapi.Field(
            name="name_user",
            required=True,
            location="form",
            schema=coreschema.String(description='Name the user register.')
        ),
        coreapi.Field(
            name="last_name_user",
            required=True,
            location="form",
            schema=coreschema.String(description='Last name the user register.')
        ),
        coreapi.Field(
            name="year_user",
            required=True,
            location="form",
            schema=coreschema.Integer(description='Year the user register.')
        ),
        coreapi.Field(
            name="type_user",
            required=True,
            location="form",
            schema=coreschema.String(description='Type the user register.')
        ),
    ]
))
def register(request):
    """
    Endpoint for user registration.
    """
    serializer = UsersSerializer(data=request.data)

    if serializer.is_valid():
        # Crear una instancia de Dispensa
        dispensa = Dispensa.objects.create()
        
        # Asignar la dispensa al usuario
        serializer.save(dispensa=dispensa)
        
        return Response(serializer.data, status=201)

    return Response(serializer.errors, status=400)

# Function register buys of the ticket
@api_view(['POST'])
@schema(AutoSchema(
    manual_fields=[
        coreapi.Field(
            name="user_id",
            required=True,
            location="form",
            schema=coreschema.Integer(description='User ID.')
        ),
        coreapi.Field(
            name="file",
            required=True,
            location="form",
            schema=coreschema.String(description='PDF file of the ticket.')
        ),
    ]
))
def getinto_ticket(request):
    user_id = request.data.get('user_id')
    pdf_file = request.FILES.get('file')

    if not user_id or not pdf_file:
        return Response({'error': 'User ID and PDF file are required.'}, status=400)


    with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{user_id}.pdf") as temp_pdf:
        for chunk in pdf_file.chunks():
            temp_pdf.write(chunk)
        temp_pdf_path = temp_pdf.name

    
    return Response({'message': 'PDF file received successfully.', 'temp_pdf_path': temp_pdf_path}, status=200)

# Function to join aliment manually
@api_view(['POST'])
@schema(AutoSchema(
    manual_fields=[
        coreapi.Field(
            name="user_id",
            required=True,
            location="form",
            schema=coreschema.Integer(description='User ID.')
        ),
        coreapi.Field(
            name="name_aliment",
            required=True,
            location="form",
            schema=coreschema.String(description='Name of the aliment.')
        ),
        coreapi.Field(
            name="unit_measurement",
            required=True,
            location="form",
            schema=coreschema.String(description='Unit of measurement.')
        ),
        coreapi.Field(
            name="load_alimento",
            required=True,
            location="form",
            schema=coreschema.Integer(description='Load of the aliment.')
        ),
    ]
))
def join_aliment(request):
    user_id = request.data.get('user_id')
    name_alimento = request.data.get('name_aliment')
    unit_measurement = request.data.get('unit_measurement')
    load_alimento = request.data.get('load_alimento')

    # Validar que todos los campos estén presentes
    if not all([user_id, name_alimento, unit_measurement, load_alimento]):
        return Response({'error': 'All fields are required.'}, status=400)

    try:
        user = Users.objects.get(id_user=user_id)
        dispensa = user.dispensa
        if not dispensa:
            return Response({'error': 'User does not have a dispensa.'}, status=404)
    except Users.DoesNotExist:
        return Response({'error': 'User not found.'}, status=404)

    # Crear el alimento
    alimento = Alimento.objects.create(
        name_alimento=name_alimento,
        unit_measurement=unit_measurement,
        load_alimento=load_alimento
    )

    # Asociar el alimento a la dispensa en la tabla intermedia
    dispensa_alimento, created = DispensaAlimento.objects.get_or_create(dispensa=dispensa, alimento=alimento)

    return Response({'message': 'Alimento added successfully.', 'alimento': {
        'id_alimento': alimento.id_alimento,
        'name_alimento': alimento.name_alimento,
        'unit_measurement': alimento.unit_measurement,
        'load_alimento': alimento.load_alimento
    }}, status=201)

@api_view(['GET'])
@schema(AutoSchema(
    manual_fields=[
        coreapi.Field(
            name="user_id",
            required=True,
            location="query",
            schema=coreschema.Integer(description='User ID.')
        ),
        coreapi.Field(
            name="dispensa_id",
            required=True,
            location="query",
            schema=coreschema.Integer(description='Dispensa ID.')
        ),
    ]
))
def dispensa_detail(request):
    user_id = request.query_params.get('user_id')
    dispensa_id = request.query_params.get('dispensa_id')

    if not user_id or not dispensa_id:
        return Response({'error': 'User ID and Dispensa ID are required.'}, status=400)

    try:
        user_id = int(user_id)
        dispensa_id = int(dispensa_id)
    except ValueError:
        return Response({'error': 'User ID and Dispensa ID must be integers.'}, status=400)

    try:
        user = Users.objects.get(id_user=user_id)
    except Users.DoesNotExist:
        return Response({'error': 'User not found.'}, status=404)

    try:
        dispensa = Dispensa.objects.get(id_dispensa=dispensa_id, users=user)
    except Dispensa.DoesNotExist:
        return Response({'error': 'Dispensa not found for the user.'}, status=404)
    except AttributeError:
        return Response({'error': 'User does not have a dispensa.'}, status=404)

    serializer = DispensaSerializer(dispensa)
    return Response(serializer.data)