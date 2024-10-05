from rest_framework import viewsets
from rest_framework.decorators import api_view, schema
from rest_framework.response import Response
from rest_framework.schemas import AutoSchema
from django.utils import timezone
from google.cloud import vision
from openai import OpenAI
from .models import Users,Dispensa,Alimento,DispensaAlimento
from .serializer import UsersSerializer,DispensaSerializer
import coreapi
import coreschema
import pytz
import tempfile
import os
import json


#Cargar las keys para google OCT y ChatGPT
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "E://Informatica//AppMinutIA//Backend//ocrappminutia-e3a23be500d4.json"
#openai.api_key = os.getenv("OPENAI_API_KEY")


## REGISTRO DE USUARIOS

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
        name="user_type",
        required=True,
        location="form",
        schema=coreschema.Enum(
            enum=["trabajador", "estudiante","dueño de casa"],
            description='Type the user register. Allowed values: trabajador, estudiante, dueño de casa.'
    )
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

## cONTROL DE ALIMENTOS    

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
    
    client = vision.ImageAnnotatorClient()

    # Cargar la imagen desde un archivo local
    with open(temp_pdf_path, 'rb') as image_file:
        content = image_file.read()
    
    image = vision.Image(content=content)
    response = client.text_detection(image=image)

    if response.error.message:
        return Response({'error': response.error.message}, status=400)  
    
     # Extraer el texto del OCR
    extracted_text = response.full_text_annotation.text

    client = OpenAI()
    
    # Prompt para la IA
    prompt = f"""
    Tengo la siguiente boleta de supermercado: '{extracted_text}'.
    Extrae los alimentos, la unidad de medida (kg, gr, lt, ml) y la cantidad. Responde en formato JSON de la siguiente manera:
    [
      {{ "producto": "nombre del producto","unidad": "kg o gr o lt o ml","cantidad": "cantidad" }},
     ...
    ]
    en caso que no puedas determinar la unidad de medida asignar "unidad": "kg" o "unidad": "lt" dependiendo del caso 
    """

    completion = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {
            "role": "user",
            "content": prompt
        }
    ])

    # Obtener la respuesta de OpenAI
    openai_response = completion.choices[0].message.content

    # Extraer el contenido JSON de la respuesta
    json_start = openai_response.find('```json') + len('```json')
    json_end = openai_response.rfind('```')
    json_content = openai_response[json_start:json_end].strip()

    # Parsear la respuesta JSON
    alimentos = json.loads(json_content)

    #Guardar los alimentos en la base de datos
    try:
        user = Users.objects.get(id_user=user_id)
        dispensa = user.dispensa
        if not dispensa:
            return Response({'error': 'User does not have a dispensa.'}, status=404)
    except Users.DoesNotExist:
        return Response({'error': 'User not found.'}, status=404)

    alimentos_guardados = []
    for alimento_data in alimentos:
        alimento = Alimento.objects.create(
            name_alimento=alimento_data['producto'],
            unit_measurement=alimento_data['unidad'],
            load_alimento=alimento_data['cantidad']
        )
        DispensaAlimento.objects.get_or_create(dispensa=dispensa, alimento=alimento)
        alimentos_guardados.append({
            'producto': alimento.name_alimento,
            'unidad': alimento.unit_measurement,
            'cantidad': alimento.load_alimento
        })


    # Actualizar el campo de última actualización de la dispensa
    dispensa.ultima_actualizacion = timezone.now()
    dispensa.save()

    # Eliminar el archivo PDF temporal
    os.remove(temp_pdf_path)

    return Response({'Message': 'Ingreso de alimentos exitoso'}, status=200)

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

    # Actualizar el campo de última actualización de la dispensa
    dispensa.ultima_actualizacion = timezone.now()
    dispensa.save()

    return Response({'message': 'Alimento added successfully.', 'alimento': {
        'id_alimento': alimento.id_alimento,
        'name_alimento': alimento.name_alimento,
        'unit_measurement': alimento.unit_measurement,
        'load_alimento': alimento.load_alimento
    }}, status=201)

@api_view(['DELETE'])
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
        coreapi.Field(
            name="alimento_id",
            required=True,
            location="query",
            schema=coreschema.Integer(description='Alimento ID.')
        ),
    ]
))
def delete_alimento(request):
    user_id = request.query_params.get('user_id')
    dispensa_id = request.query_params.get('dispensa_id')
    alimento_id = request.query_params.get('alimento_id')

    if not all([user_id, dispensa_id, alimento_id]):
        return Response({'error': 'User ID, Dispensa ID and Alimento ID are required.'}, status=400)

    try:
        user_id = int(user_id)
        dispensa_id = int(dispensa_id)
        alimento_id = int(alimento_id)
    except ValueError:
        return Response({'error': 'User ID, Dispensa ID and Alimento ID must be integers.'}, status=400)

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

    try:
        alimento = Alimento.objects.get(id_alimento=alimento_id)
    except Alimento.DoesNotExist:
        return Response({'error': 'Alimento not found.'}, status=404)

    try:
        dispensa_alimento = DispensaAlimento.objects.get(dispensa=dispensa, alimento=alimento)
    except DispensaAlimento.DoesNotExist:
        return Response({'error': 'Alimento not found in the dispensa.'}, status=404)

    dispensa_alimento.delete()

    # Actualizar el campo de última actualización de la dispensa
    dispensa.ultima_actualizacion = timezone.now()
    dispensa.save()

    return Response({'message': 'Alimento deleted successfully.'}, status=200)

#Eliminacion masiva de alimentos


#EDITAR ALIMENTO
@api_view(['PUT'])
@schema(AutoSchema(
    manual_fields=[
        coreapi.Field(
            name="user_id",
            required=True,
            location="form",
            schema=coreschema.Integer(description='User ID.')
        ),
        coreapi.Field(
            name="dispensa_id",
            required=True,
            location="form",
            schema=coreschema.Integer(description='Dispensa ID.')
        ),
        coreapi.Field(
            name="alimento_id",
            required=True,
            location="form",
            schema=coreschema.Integer(description='Alimento ID.')
        ),
        coreapi.Field(
            name="name_alimento",
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
def edit_alimento(request):
    user_id = request.data.get('user_id')
    dispensa_id = request.data.get('dispensa_id')
    alimento_id = request.data.get('alimento_id')
    name_alimento = request.data.get('name_alimento')
    unit_measurement = request.data.get('unit_measurement')
    load_alimento = request.data.get('load_alimento')

    if not all([user_id, dispensa_id, alimento_id, name_alimento, unit_measurement, load_alimento]):
        return Response({'error': 'All fields are required.'}, status=400)

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

    try:
        alimento = Alimento.objects.get(id_alimento=alimento_id)
    except Alimento.DoesNotExist:
        return Response({'error': 'Alimento not found.'}, status=404)

    alimento.name_alimento = name_alimento
    alimento.unit_measurement = unit_measurement
    alimento.load_alimento = load_alimento
    alimento.save()

    # Actualizar el campo de última actualización de la dispensa
    dispensa.ultima_actualizacion = timezone.now()
    dispensa.save()

    return Response({'message': 'Alimento updated successfully.', 'alimento': {
        'id_alimento': alimento.id_alimento,
        'name_alimento': alimento.name_alimento,
        'unit_measurement': alimento.unit_measurement,
        'load_alimento': alimento.load_alimento
    }}, status=200)
    

##  DISPENSA    

#CONSULTAR DISPENSA
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

    # Convertir la hora a la zona horaria local (Santiago) para la respuesta
    santiago_tz = pytz.timezone('America/Santiago')
    ultima_actualizacion_local = dispensa.ultima_actualizacion.astimezone(santiago_tz)

    # Serializar la dispensa
    serializer = DispensaSerializer(dispensa)
    data = serializer.data
    data['ultima_actualizacion'] = ultima_actualizacion_local.strftime('%Y-%m-%d %H:%M:%S %Z%z')

    return Response(data)

# MINUTA DE ALIMENTOS

#CREAR MINUTA DE ALIMENTOS
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
            name="dispensa_id",
            required=True,
            location="form",
            schema=coreschema.Integer(description='Dispensa ID.')
        ),
    ]
))
def create_meinuta(request):
    user_id = request.data.get('user_id')
    dispensa_id = request.data.get('dispensa_id')

    
    return Response({'mensasage': 'Operativo'}, status=202)

#CONSULTAR MINUTA DE ALIMENTOS
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
def minuta_detail(request):
    user_id = request.query_params.get('user_id')
    dispensa_id = request.query_params.get('dispensa_id')


    return Response({'mensasage': 'Operativo'}, status=202)

#ELIMINAR MINUTA DE ALIMENTOS
@api_view(['DELETE'])
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
def delete_minuta(request):
    user_id = request.query_params.get('user_id')
    dispensa_id = request.query_params.get('dispensa_id')
    
    return Response({'mensasage': 'Operativo'}, status=202)

#CONSULTAR HISTORIAL DE MINUTA DE ALIMENTOS
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
def minuta_history(request):
    user_id = request.query_params.get('user_id')
    dispensa_id = request.query_params.get('dispensa_id')
    
    return Response({'mensasage': 'Operativo'}, status=202)

## CONSULTAR RECETAS DE ALIMENTOS 
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
            name="dispensa_id",
            required=True,
            location="form",
            schema=coreschema.Integer(description='Dispensa ID.')
        ),
    ]
))
def get_receta(request):
    user_id = request.data.get('user_id')
    dispensa_id = request.data.get('dispensa_id')
    
    return Response({'mensasage': 'Operativo'}, status=202)


