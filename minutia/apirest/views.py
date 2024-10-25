from rest_framework import viewsets
from rest_framework.decorators import api_view, schema
from rest_framework.response import Response
from rest_framework.schemas import AutoSchema
from django.utils import timezone
from google.cloud import vision
from openai import OpenAI
from .models import Users,Dispensa,Alimento,DispensaAlimento,ListaMinuta,Minuta,InfoMinuta
from .serializer import UsersSerializer,DispensaSerializer
from .notificaciones import verificar_estado_minuta, verificar_dispensa
from langchain import OpenAI
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
import coreapi
import coreschema
import pytz
import tempfile
import os
import json
from datetime import datetime
from dateutil import parser


#Cargar las keys para google OCT y ChatGPT
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "E://Informatica//AppMinutIA//Backend//ocrappminutia-e3a23be500d4.json"
openai_key = os.getenv("OPENAI_API_KEY")

# Cargar el modelo de OpenAI
llm = ChatOpenAI(model_name="gpt-3.5-turbo", api_key=openai_key)


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
            schema=coreschema.Integer(description='Year old the user that register.')
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
        coreapi.Field(
            name="user_sex",
            required=True,
            location="form",
            schema=coreschema.Enum(
                enum=["masculino", "femenino"],
                description="sex the user register. Allowed values: masculino, femenino."
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

    # Prompt para la IA
    # Definir el template del prompt
    template = """
    Tengo la siguiente boleta de supermercado: '{extracted_text}'.
    Extrae los alimentos, la unidad de medida (kg, gr, lt, ml) y la cantidad. Responde en formato JSON de la siguiente manera:
    [
    {{ "producto": "nombre del producto", "unidad": "kg o gr o lt o ml", "cantidad": "cantidad" }}
    ]
    En caso que no puedas determinar la unidad de medida, asignar "unidad": "kg" o "unidad": "lt" dependiendo del caso.
    """
    prompt = PromptTemplate(input_variables=["extracted_text"], template=template)
    formatted_prompt = prompt.format(extracted_text=extracted_text)
    
    # Cambia el uso de 'llm' para usar 'invoke'
    llm_response = llm.invoke(formatted_prompt)

    # Accede al contenido del mensaje, si es necesario
    json_content = llm_response.content.strip()

    # Parsear la respuesta JSON
    try:
        alimentos = json.loads(json_content)
    except json.JSONDecodeError:
        return Response({'error': 'Invalid JSON format.'}, status=400)

    # Validar que los alimentos tengan valores válidos
    for alimento in alimentos:
        if not alimento['cantidad'].replace('.', '', 1).isdigit():
            return Response({'error': f"El valor de cantidad para el producto {alimento['producto']} no es válido."}, status=400)

    # Guardar los alimentos en la base de datos
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
    #return Response(json_content, status=200)
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
    
    #control de error de datos ingresados
    # valiudar que load_alimento sea decimal
    if not load_alimento.replace('.', '', 1).isdigit():
        return Response({'error': 'Load alimento must be a decimal number.'}, status=400)
    
    # control unit_measurement
    if unit_measurement not in ['kg', 'gr', 'lt', 'ml']:
        return Response({'error': 'Unit measurement must be kg, gr, lt or ml.'}, status=400)


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
def delete_all_alimentos(request):
    user_id = request.query_params.get('user_id')
    dispensa_id = request.query_params.get('dispensa_id')
    
     # Validar que los campos sean del tipo integer
    try:
        user_id = int(user_id)
        dispensa_id = int(dispensa_id)
    except (ValueError, TypeError):
        return Response({'error': 'User ID and Dispensa ID must be integers.'}, status=400)

    if not all([user_id, dispensa_id]):
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

    # Eliminar todos los alimentos de la dispensa
    DispensaAlimento.objects.filter(dispensa=dispensa).delete()

    # Actualizar el campo de última actualización de la dispensa
    dispensa.ultima_actualizacion = timezone.now()
    dispensa.save()

    return Response({'message': 'All alimentos deleted successfully.'}, status=200)

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
    
    # Validar que load_alimento sea decimal
    if not load_alimento.replace('.', '', 1).isdigit():
        return Response({'error': 'Load alimento must be a decimal number.'}, status=400)
    
    # Validar que unit_measurement sea kg, gr, lt o ml
    if unit_measurement not in ['kg', 'gr', 'lt', 'ml']:
        return Response({'error': 'Unit measurement must be kg, gr, lt or ml.'}, status=400)
    

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

# CREAR MINUTA DE ALIMENTOS
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
        coreapi.Field(
            name='start_date',
            required=True,
            location='form',
            schema=coreschema.String(description='Start date of the minuta.')
        ),
        coreapi.Field(
            name="people_number",
            required=True,
            location="form",
            schema=coreschema.Integer(description='Number of people.')
        ),
        coreapi.Field(
            name="dietary_preference",
            required=True,
            location="form",
            schema=coreschema.String(description='Dietary preference.')
        ),
        coreapi.Field(
            name="type_food",
            required=True,
            location="form",
            schema=coreschema.String(description='Type of food. Allowed values: desayuno, almuerzo and/or cena.')
        ),
    ]
))
def create_meinuta(request):
    user_id = request.data.get('user_id')
    dispensa_id = request.data.get('dispensa_id')
    date_start = request.data.get('start_date')
    people_number = request.data.get('people_number')
    dietary_preference = request.data.get('dietary_preference')
    type_food = request.data.get('type_food')

    if not all([ user_id, dispensa_id, date_start, people_number, dietary_preference, type_food]):
        return Response({'error': 'All fields are required.'}, status=400)

    
    name_lista_minuta = f"Minuta {timezone.now().strftime('%d-%m-%Y')}"

    # Validar el formato de la fecha de inicio
    try:
        date_start = datetime.strptime(date_start, '%Y-%m-%d').date()
    except ValueError:
        return Response({'error': 'Invalid date format. Use YYYY-MM-DD.'}, status=400)
    
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
    
    #validar que no tenga una minuta activa
    try:
        lista_minuta = ListaMinuta.objects.get(user=user, state_minuta=True)
        return Response({'error': 'User already has an active minuta.'}, status=400)
    except ListaMinuta.DoesNotExist:
        pass
    
    # Obtener los alimentos asociados a la despensa
    alimentos_list = dispensa.get_alimentos_details()
    

    if not alimentos_list:
        return Response({'error': 'No alimentos found in the dispensa.'}, status=400)
    

    # se crea el prompt para la api
    starting_date =  date_start
    template = """
    Tengo la siguiente despensa: '{alimentos_list}'. Solo puedes utilizar estos ingredientes.
    Necesito una minuta para {people_number} personas con preferencia {dietary_preference} que incluya {type_food} para los días que alcance la comida, comenzando desde {starting_date}.
    Las fechas deben ser consecutivas y no deben faltar días. Calcula cuántos días puede durar la minuta en función de la cantidad de alimentos disponible. Utiliza la cantidad adecuada de ingredientes por día.
    Responde únicamente en formato JSON. No hagas preguntas ni incluyas información adicional. Proporciona la respuesta en el siguiente formato JSON:
    [
       {{ "name_food": "nombre del plato" ,
       "type_food": "tipo de comida",
       "fecha": ""YYYY-MM-DD""}}     
    ]
    """

    prompt = PromptTemplate(input_variables=["extracted_text","alimentos_list", "people_number", "dietary_preference", "type_food", "starting_date"], template=template)
    formatted_prompt = prompt.format(alimentos_list=alimentos_list, people_number=people_number, dietary_preference=dietary_preference, type_food=type_food, starting_date=starting_date)
    
    # Cambia el uso de 'llm' para usar 'invoke'
    llm_response = llm.invoke(formatted_prompt)

    # Accede al contenido del mensaje, si es necesario
    json_content = llm_response.content.strip()
   

    # Parsear la respuesta JSON
    try:
        minutas = json.loads(json_content)
    except json.JSONDecodeError:
        return Response({'error': 'Invalid JSON format.'}, status=400)
    
    if not minutas:
        return Response({'error': 'No minutas found in the response.'}, status=400)

    # Extraer la última fecha de la minuta y convertirla a un objeto datetime
    fecha_termino_str = minutas[-1]['fecha']
    try:
        fecha_termino = parser.parse(fecha_termino_str)
        fecha_termino = fecha_termino.replace(tzinfo=pytz.UTC)  # Asegurarse de que esté en UTC
    except (ValueError, parser.ParserError) as e:
        return Response({'error': f'Invalid date format in minutas: {str(e)}'}, status=400)

    # Crear la lista de minuta y asociarla a los alimentos
    lista_minuta = ListaMinuta.objects.create(
        user=user,
        nombre_lista_minuta=name_lista_minuta,
        fecha_creacion=timezone.now(),
        fecha_inicio=starting_date,
        fecha_termino=fecha_termino,
        state_minuta=True  # Asumiendo que es un booleano
    )

    # cargar datos a info minuta
    InfoMinuta.objects.create(
        lista_minuta=lista_minuta,
        tipo_dieta=dietary_preference,
        cantidad_personas=people_number
    )

    for minuta_data in minutas:
        try:
            fecha_minuta = parser.parse(minuta_data['fecha'])
        except (ValueError, parser.ParserError) as e:
            return Response({'error': f'Invalid date format in minuta: {str(e)}'}, status=400)
        
        Minuta.objects.create(
            lista_minuta=lista_minuta,
            type_food=minuta_data['type_food'],
            name_food=minuta_data['name_food'],
            fecha=fecha_minuta
        )

    # Convertir la hora a la zona horaria local (Santiago) para la respuesta
    #santiago_tz = pytz.timezone('America/Santiago')
    fecha_inicio_local = lista_minuta.fecha_inicio
    fecha_termino_local = lista_minuta.fecha_termino

    # Formatear las fechas de las minutas para la respuesta
    minutas_data = [
        {
            'type_food': minuta.type_food,
            'name_food': minuta.name_food,
            'fecha': minuta.fecha
        } for minuta in lista_minuta.minutas.all()
    ]

    return Response({
        'message': 'Minutas added successfully.',
        'lista_minuta': {
            'id_lista_minuta': lista_minuta.id_lista_minuta,
            'nombre_lista_minuta': lista_minuta.nombre_lista_minuta,
            'fecha_inicio': fecha_inicio_local.strftime('%Y-%m-%d %H:%M:%S %Z%z'),
            'fecha_inicio': fecha_inicio_local.strftime('%Y-%m-%d %H:%M:%S %Z%z'),
            'fecha_termino': fecha_termino_local,
            'state_minuta': lista_minuta.state_minuta
        },
        'minutas': minutas_data
    }, status=201)

#COSULTA si hay una minuta activa
@api_view(['GET'])
@schema(AutoSchema(
    manual_fields=[
        coreapi.Field(
            name="user_id",
            required=True,
            location="query",
            schema=coreschema.Integer(description='User ID.')
        ),
    ]
))
def active_minuta(request):

    user_id = request.query_params.get('user_id')

    if not user_id:
        return Response({'error': 'User ID is required.'}, status=400)

    try:
        user = Users.objects.get(id_user=user_id)
    except Users.DoesNotExist:
        return Response({'error': 'User not found.'}, status=404)

    try:
        lista_minuta = ListaMinuta.objects.get(user=user, state_minuta=True)
    except ListaMinuta.DoesNotExist:
        return Response({'state_minuta': 'False'}, status=404)

    return Response({'state_minuta': 'True'}, status=200)
 
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
    ]
))
def minuta_detail(request):
    user_id = request.query_params.get('user_id')
    
    # Validar que el campo esté presente
    if not user_id:
        return Response({'error': 'User ID is required.'}, status=400)
    
    try:
        user = Users.objects.get(id_user=user_id)
    except Users.DoesNotExist:
        return Response({'error': 'User not found.'}, status=404)
    
    # Obtener la última minuta activa del usuario
    try:
        lista_minuta = ListaMinuta.objects.get(user=user, state_minuta=True)
    except ListaMinuta.DoesNotExist:
        return Response({'state_minuta':'False','error': 'No active minuta found for the user.'}, status=404)

    #obtenere la informacion de la minuta
    info_minuta = InfoMinuta.objects.get(lista_minuta=lista_minuta)
    
    # Convertir la hora a la zona horaria local (Santiago) para la respuesta
    santiago_tz = pytz.timezone('America/Santiago')
    fecha_inicio_local = lista_minuta.fecha_inicio 
    fecha_termino_local = lista_minuta.fecha_termino

    # Formatear las fechas de las minutas para la respuesta
    minutas_data = [
        {
            'id_minuta': minuta.id_minuta,
            'type_food': minuta.type_food,
            'name_food': minuta.name_food,
            'fecha': minuta.fecha
        } for minuta in lista_minuta.minutas.all()
    ]

    return Response({
        'state_minuta': lista_minuta.state_minuta,
        'lista_minuta': {
            'id_lista_minuta': lista_minuta.id_lista_minuta,
            'nombre_lista_minuta': lista_minuta.nombre_lista_minuta,
            'fecha_creacion': lista_minuta.fecha_creacion,
            'fecha_inicio': fecha_inicio_local.strftime('%Y-%m-%d'),
            'fecha_termino': fecha_termino_local,
            

        },
        'info_minuta': {
            'tipo_dieta': info_minuta.tipo_dieta,
            'cantidad_personas': info_minuta.cantidad_personas
        },
        'minutas': minutas_data
    })


#ELIMINAR MINUTA DE ALIMENTOS
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
            name="ListaMinuta_id",
            required=True,
            location="form",
            schema=coreschema.Integer(description='ListaMinuta ID.')
        ),
        
    ]
))
def desactivate_minuta(request):
    user_id = request.query_params.get('user_id')
    id_lista_minuta = request.query_params.get('ListaMinuta_id')

    # Validar que todos los campos estén presentes
    if not all([user_id, id_lista_minuta]):
        return Response({'error': 'User ID and ListaMinuta ID are required.'}, status=400)
    
    try:
        user = Users.objects.get(id_user=user_id)
    except Users.DoesNotExist:
        return Response({'error': 'User not found.'}, status=404)
    
    try:
        lista_minuta = ListaMinuta.objects.get(id_lista_minuta=id_lista_minuta, user=user)
    except ListaMinuta.DoesNotExist:
        return Response({'error': 'ListaMinuta not found for the user.'}, status=404)
    
    # Cambiar estado de la minuta a inactivo
    lista_minuta.state_minuta = False
    lista_minuta.save()

    # Verificar si el estado se ha actualizado correctamente
    if not lista_minuta.state_minuta:
        return Response({'message': 'Minuta is deactivated.'}, status=200)
    else:
        return Response({'error': 'Failed to deactivate Minuta.'}, status=500)

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
    ]
))
def minuta_history(request):
    user_id = request.query_params.get('user_id')
    
    # Traer todas las minutas del usuario
    try:
        user = Users.objects.get(id_user=user_id)
    except Users.DoesNotExist:
        return Response({'error': 'User not found.'}, status=404)
    
    minutas = ListaMinuta.objects.filter(user=user)
    info_minutas = InfoMinuta.objects.filter(lista_minuta__in=minutas)

    # Convertir la hora a la zona horaria local (Santiago) para la respuesta
    santiago_tz = pytz.timezone('America/Santiago')
    minutas_data = []

    for minuta in minutas:
        fecha_inicio_local = minuta.fecha_inicio 
        fecha_termino_local = minuta.fecha_termino
        
        # Obtener la información de InfoMinuta asociada a la ListaMinuta
        info_minuta = info_minutas.filter(lista_minuta=minuta).first()
        
        if info_minuta:
            info_minuta_data = {
                'tipo_dieta': info_minuta.tipo_dieta,
                'cantidad_personas': info_minuta.cantidad_personas
            }
        else:
            info_minuta_data = None

        minutas_data.append({
            'id_lista_minuta': minuta.id_lista_minuta,
            'nombre_lista_minuta': minuta.nombre_lista_minuta,
            'fecha_creacion': minuta.fecha_creacion,
            'fecha_inicio': fecha_inicio_local.strftime('%Y-%m-%d'),
            'fecha_termino': fecha_termino_local,
            'state_minuta': minuta.state_minuta,
            'info_minuta': info_minuta_data
        })

    return Response({'minutas': minutas_data}, status=200)

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
            name="id_lista_minuta",
            required=True,
            location="form",
            schema=coreschema.Integer(description='id_lista_minuta')
        ),
        coreapi.Field(
            name="id_alimento",
            required=True,
            location="form",
            schema=coreschema.Integer(description='id Alimento.')
        ),
    ]
))
def get_receta(request):
    user_id = request.data.get('user_id')
    id_alimento = request.data.get('id_alimento')
    id_lista_minuta = request.data.get('id_lista_minuta')

    if not all([user_id, id_alimento, id_lista_minuta]):
        return Response({'error': 'All fields are required.'}, status=400)

    try:
        user = Users.objects.get(id_user=user_id)
    except Users.DoesNotExist:
        return Response({'error': 'User not found.'}, status=404)

    try:
        lista_minuta = ListaMinuta.objects.get(id_lista_minuta=id_lista_minuta, user=user)
    except ListaMinuta.DoesNotExist:
        return Response({'error': 'ListaMinuta not found for the user.'}, status=404)
    
    try:
        info_minuta = InfoMinuta.objects.get(lista_minuta=lista_minuta)
    except InfoMinuta.DoesNotExist:
        return Response({'error': 'InfoMinuta not found for the ListaMinuta.'}, status=404)

    try:
        minuta = Minuta.objects.get(id_minuta=id_alimento, lista_minuta=lista_minuta)
    except Minuta.DoesNotExist:
        return Response({'error': 'Alimento not found in the minuta.'}, status=404)

    # Obtener nombre del alimento
    name_minuta = minuta.name_food
    # Obtener número de personas 
    people_number = info_minuta.cantidad_personas

    

    

    # Crear el prompt para la API
    template ="""
    Proporciona la receta {name_minuta} para la cantidad de {people_number} personas. La receta debe ser devuelta en formato JSON, siguiendo esta estructura:

    {{
      "ingredientes": [
        {{ "nombre": "ingrediente1", "cantidad": "cantidad1" }},
        {{ "nombre": "ingrediente2", "cantidad": "cantidad2" }},
        ...
      ],
      "paso_a_paso": [
        "Paso 1: descripción del primer paso",
        "Paso 2: descripción del segundo paso",
        ...
      ]
    }}
    Usa solo los ingredientes y pasos esenciales para crear el plato.
    """

    prompt = PromptTemplate(input_variables=[ "name_minuta", "people_number"], template=template)
    formatted_prompt = prompt.format( name_minuta=name_minuta, people_number=people_number)
    
    # Cambia el uso de 'llm' para usar 'invoke'
    llm_response = llm.invoke(formatted_prompt)

    # Accede al contenido del mensaje, si es necesario
    json_content = llm_response.content.strip()

    # Parsear la respuesta JSON
    try:
        receta = json.loads(json_content)
    except json.JSONDecodeError:
        return Response({'error': 'Invalid JSON format in the response.'}, status=400)

    return Response({'receta': receta}, status=200)

# NOTIFICACIONES

#CONSULTAR NOTIFICACIONES
@api_view(['GET'])
@schema(AutoSchema(
    manual_fields=[
        coreapi.Field(
            name="user_id",
            required=True,
            location="query",
            schema=coreschema.Integer(description='User ID.')
        ),
    ]
))
def obtener_notificacion(request):
    usuario = request.query_params.get('user_id')
    print(usuario)
    mensaje = verificar_estado_minuta(usuario)
    print(mensaje)
    if mensaje:
        return Response({"notificacion": mensaje}, status=200)
    else:
        return Response({"notificacion": "No tienes nuevas notificaciones"}, status=200)

    
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
def obtener_notificacion_dispensa(request):
    user_id = request.query_params.get('user_id')
    dispensa_id = request.query_params.get('dispensa_id')
    mensaje = verificar_dispensa(user_id,dispensa_id)
    if mensaje:
        return Response({"notificacion": mensaje}, status=200)
    else:
        return Response({"notificacion": "No tienes nuevas notificaciones"}, status=200)
