from rest_framework import viewsets
from rest_framework.decorators import api_view, schema
from rest_framework.response import Response
from rest_framework.schemas import AutoSchema
from django.utils import timezone
from google.cloud import vision
from .models import ProgresoObjetivo, TipoObjetivo, Users,Dispensa,Alimento,DispensaAlimento,ListaMinuta,Minuta,InfoMinuta,MinutaIngrediente,Sugerencias,HistorialAlimentos,Objetivo
from .serializer import ObjetivoSerializer, UsersSerializer, DispensaSerializer, ProgresoObjetivoSerializer
from .helpers.notificaciones import verificar_estado_minuta, verificar_dispensa, verificar_alimentos_minuta, notificacion_sugerencia
from .helpers.controlminuta import editar_cantidad_ingrediente_minuta, minimoalimentospersona, alimentos_desayuno, listproduct_minutafilter,obtener_y_validar_minuta_del_dia, update_estado_dias
from .helpers.procesoia import crear_recomendacion_compra, extractdataticket, analyzeusoproductos, makeminuta, getreceta
from .helpers.Metricas import calcular_uso_frecuente_por_comida, data_minima_recomendacion_compra,obtener_dieta_mas_usada,typo_food_mas_utlizado
from .helpers.ControlObjetivos import control_objetivo_minuta
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
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.getenv("RUTA_KEY_API_VISION")
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
    name_user = request.data.get('name_user')
    last_name_user = request.data.get('last_name_user')
    year_user = request.data.get('year_user')
    user_type = request.data.get('user_type')
    
    if not all([name_user, last_name_user, year_user, user_type]):
        return Response({'error': 'No fueron completados toddos los campos.'}, status=400)

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
    """
    Endpoint for registering the purchase of a ticket.
    """
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

    #ejecutar funcion modulada para extraer la data
    alimentos = extractdataticket(extracted_text)

    #ejecutar asignacion de alimentos a la dispensa
    alimentos = analyzeusoproductos(alimentos)

    #correcion de aliomentos de desayuno
    alimentos = alimentos_desayuno(alimentos)
    
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
            load_alimento=alimento_data['cantidad'],
            uso_alimento=alimento_data['uso_alimento']
        )
        DispensaAlimento.objects.get_or_create(dispensa=dispensa, alimento=alimento)
        alimentos_guardados.append({
            'producto': alimento.name_alimento,
            'unidad': alimento.unit_measurement,
            'cantidad': alimento.load_alimento,
            'uso_alimento': alimento.uso_alimento
        })

    # Actualizar el campo de última actualización de la dispensa
    dispensa.ultima_actualizacion = timezone.now()
    dispensa.save() 

    # guardar alimentos en tabla de HistorialAlimentos
    for alimento in alimentos_guardados:
        HistorialAlimentos.objects.create(
            name_alimento=alimento['producto'],
            unit_measurement=alimento['unidad'],
            load_alimento=alimento['cantidad'],
            uso_alimento=alimento['uso_alimento'],
            user_id=user.id_user,
        )
        

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
        coreapi.Field(
            name="uso_alimento",
            required=True,
            location="form",
            schema=coreschema.String(description='Use of the aliment.')
        ),
    ]
))
def join_aliment(request):
    """
    Endpoint for manually adding an aliment to the despensa.
    """
    user_id = request.data.get('user_id')
    name_alimento = request.data.get('name_aliment')
    unit_measurement = request.data.get('unit_measurement')
    load_alimento = request.data.get('load_alimento')
    uso_alimento = request.data.get('uso_alimento')

    # Validar que todos los campos estén presentes
    if not all([user_id, name_alimento, unit_measurement, load_alimento, uso_alimento]):
        return Response({'error': 'All fields are required.'}, status=400)
    
    #control de error de datos ingresados
    # valiudar que load_alimento sea decimal
    if not load_alimento.replace('.', '', 1).isdigit():
        return Response({'error': 'Load alimento must be a decimal number.'}, status=400)
    
    # control unit_measurement
    if unit_measurement not in ['kg', 'gr', 'lt', 'ml']:
        return Response({'error': 'Unit measurement must be kg, gr, lt or ml.'}, status=400)
    
    # control uso_alimento
    if uso_alimento not in ['desayuno', 'almuerzo', 'cena','desayuno,almuerzo','desayuno,cena','almuerzo,cena','desayuno,almuerzo,cena']:
        return Response({'error': 'Use of the aliment must be desayuno, almuerzo, cena, desayuno, almuerzo, desayuno, cena, almuerzo, cena, desayuno, almuerzo, cena.'}, status=400)

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
        load_alimento=load_alimento,
        uso_alimento=uso_alimento
    )

    # Asociar el alimento a la dispensa en la tabla intermedia
    dispensa_alimento, created = DispensaAlimento.objects.get_or_create(dispensa=dispensa, alimento=alimento)

    # Actualizar el campo de última actualización de la dispensa
    dispensa.ultima_actualizacion = timezone.now()
    dispensa.save()

    # ingresar alimento en tabla de HistorialAlimentos
    HistorialAlimentos.objects.create(
            name_alimento=name_alimento,
            unit_measurement=unit_measurement,
            load_alimento=load_alimento,
            uso_alimento=uso_alimento,
            user_id=user_id,
        )
        

    return Response({'message': 'Alimento added successfully.', 'alimento': {
        'id_alimento': alimento.id_alimento,
        'name_alimento': alimento.name_alimento,
        'unit_measurement': alimento.unit_measurement,
        'load_alimento': alimento.load_alimento,
        'uso_alimento': alimento.uso_alimento
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
    """
    Endpoint for deleting an aliment from the despensa
    in case the aliment is in a active minuta, the minuta is deactivated if the aliment is deleted
    In app have to alert the user that the aliment is in a active minuta and is going to be deactivated
    """
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
    
    #validar si el alimento esta en una minuta activa en caso de que este y se quiera eliminar se desactiva la minuta
    
    try:
        # Verificar si hay alimentos en la minuta
        alimentos_dispensa = DispensaAlimento.objects.filter(dispensa=dispensa).values_list('alimento_id', flat=True)
        # Verificar si el alimento a eliminar está en la minuta
        if alimento_id in alimentos_dispensa:
            lista_minuta = ListaMinuta.objects.get(user=user, state_minuta=True)
            info_minuta = InfoMinuta.objects.get(lista_minuta=lista_minuta.id_lista_minuta)
            alimentos_en_minuta = info_minuta.alimentos_usados_ids
            if alimento_id in alimentos_en_minuta:
                alimentos_en_minuta.remove(alimento_id)
                info_minuta.alimentos_usados_ids = alimentos_en_minuta
                info_minuta.save()
                alimentos_no_minuta = [alimento for alimento in alimentos_dispensa if alimento not in alimentos_en_minuta]
                if not alimentos_no_minuta:
                    lista_minuta.state_minuta = False
                    lista_minuta.save()
    except ListaMinuta.DoesNotExist:
        pass

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
    """
    Endpoint for deleting all alimentos from the despensa.
    """
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
    
    # si existe minuta activa y hay alimentos que estan en la minuta se desactiva la minuta
    try:
        # veificar si hay alimentos en la minuta
        alimentos_dispensa = DispensaAlimento.objects.filter(dispensa=dispensa).values_list('alimento_id', flat=True)
        lista_minuta = ListaMinuta.objects.get(user=user, state_minuta=True)
        info_minuta = InfoMinuta.objects.get(lista_minuta=lista_minuta.id_lista_minuta)
        alimentos_en_minuta = info_minuta.alimentos_usados_ids
        alimentos_no_minuta = [alimento for alimento in alimentos_dispensa if alimento not in alimentos_en_minuta]
        if alimentos_no_minuta:
            lista_minuta.state_minuta = False
            lista_minuta.save()
    except ListaMinuta.DoesNotExist:
        pass

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
        coreapi.Field(
            name="uso_alimento",
            required=True,
            location="form",
            schema=coreschema.String(description='Use of the aliment.')
        ),
    ]
))
def edit_alimento(request):
    """
    Endpoint for editing an aliment in the despensa.
    """
    user_id = request.data.get('user_id')
    dispensa_id = request.data.get('dispensa_id')
    alimento_id = request.data.get('alimento_id')
    name_alimento = request.data.get('name_alimento')
    unit_measurement = request.data.get('unit_measurement')
    load_alimento = request.data.get('load_alimento')
    uso_alimento = request.data.get('uso_alimento')

    if not all([user_id, dispensa_id, alimento_id, name_alimento, unit_measurement, load_alimento, uso_alimento]):
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
    alimento.uso_alimento = uso_alimento.lower()
    alimento.save()

    # Actualizar el campo de última actualización de la dispensa
    dispensa.ultima_actualizacion = timezone.now()
    dispensa.save()

    return Response({'message': 'Alimento updated successfully.', 'alimento': {
        'id_alimento': alimento.id_alimento,
        'name_alimento': alimento.name_alimento,
        'unit_measurement': alimento.unit_measurement,
        'load_alimento': alimento.load_alimento,
        'uso_alimento': alimento.uso_alimento
    }}, status=200)

#CONSULTAR SI HAY ALIMENTOS EN LA DISPENSA
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
def status_despensa(request):
    """
    Endpoint for checking if there are alimentos in the despensa, if there are no alimentos, return false else return true.
    """
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

    if not dispensa.alimentos.exists():
        return Response({'status': 'false'}, status=200)
    else:
        return Response({'status': 'true'}, status=200)

##  DE  SPENSA    

#CONSULTAR DESPENSA
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
def despensa_detail(request):
    """
    Endpoint for getting the details of a user's despensa.
    """
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

    # Convertir la hora a la zona horaria local (Santiago) para la respuesta
    santiago_tz = pytz.timezone('America/Santiago')
    ultima_actualizacion_local = dispensa.ultima_actualizacion.astimezone(santiago_tz)

    # Serializar la dispensa
    serializer = DispensaSerializer(dispensa)
    data = serializer.data
    data['ultima_actualizacion'] = ultima_actualizacion_local.strftime('%Y-%m-%d %H:%M:%S %Z%z')

    # Devolver en la respuesta status_in_minuta: true si está en una minuta activa y false si no está en una minuta activa
    try:
        lista_minuta = ListaMinuta.objects.get(user=user, state_minuta=True)
        info_minuta = InfoMinuta.objects.get(lista_minuta=lista_minuta.id_lista_minuta)
        productos_en_minuta = info_minuta.alimentos_usados_ids

        # Verificar si los productos de la despensa están en la minuta
        productos_en_despensa = [alimento.id_alimento for alimento in dispensa.alimentos.all()]
        status_in_minuta = {producto: (producto in productos_en_minuta) for producto in productos_en_despensa}

        # Incluir el estado en cada alimento
        for alimento in data['alimentos']:
            alimento_id = alimento['alimento']['id_alimento']
            alimento['alimento']['status_in_minuta'] = status_in_minuta.get(alimento_id, False)
    except ListaMinuta.DoesNotExist:
        for alimento in data['alimentos']:
            alimento['alimento']['status_in_minuta'] = False
    except InfoMinuta.DoesNotExist:
        for alimento in data['alimentos']:
            alimento['alimento']['status_in_minuta'] = False
    except Exception as e:
        print(f"Error al verificar el estado de la minuta: {e}")
        for alimento in data['alimentos']:
            alimento['alimento']['status_in_minuta'] = False

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
    """
    Endpoint for creating a minuta of alimentos.
    """
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
   
    # Filtrar los alimentos según el tipo de comida
    alimentos_list = listproduct_minutafilter(alimentos_list, type_food)
    print(alimentos_list)

    # Validar que tenga la cantidad de alimentos necesarios según la cantidad de personas
    errores = minimoalimentospersona(alimentos_list, people_number)
    if errores:
        print(f"Error: {errores}")
        return Response({'error': errores}, status=400)
        
    # Crear la lista de alimentos usados
    List_productos = [alimento['id'] for alimento in alimentos_list] 
    
    # asignar la fecha de inicio
    starting_date =  date_start
    
    max_attempts = 5
    attempts = 0

    while attempts < max_attempts:
        try:
            # Crear la minuta
            minutas = makeminuta(alimentos_list, people_number, dietary_preference, type_food, starting_date)
            # Extraer la última fecha de la minuta y convertirla a un objeto datetime
            fecha_termino_str = minutas[-1]['fecha']
            fecha_termino = datetime.strptime(fecha_termino_str, '%Y-%m-%d')
            fecha_termino = fecha_termino.replace(tzinfo=pytz.UTC)  # Asegurarse de que esté en UTC
            break  # Salir del bucle si no hay errores
        except Exception as e:
            print(f"Error creating minuta or parsing fecha_termino_str: {e}")
            attempts += 1
            if attempts >= max_attempts:
                return Response({'error': 'Failed to create minuta or parse fecha_termino_str after multiple attempts.'}, status=500)

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
        cantidad_personas=people_number,
        alimentos_usados_ids=List_productos,
        tipo_alimento=type_food
    )

    for minuta_data in minutas:
        try:
            fecha_minuta = parser.parse(minuta_data['fecha'])
        except (ValueError, parser.ParserError) as e:
            return Response({'error': f'Invalid date format in minuta: {str(e)}'}, status=400)
        
        minuta = Minuta.objects.create(
            lista_minuta=lista_minuta,
            type_food=minuta_data['type_food'],
            name_food=minuta_data['name_food'],
            fecha=fecha_minuta
        )
        for ingrediente in minuta_data['ingredientes']:
            MinutaIngrediente.objects.create(
                id_minuta=minuta,
                nombre_ingrediente=ingrediente['nombre'],
                tipo_medida=ingrediente['tipo_medida'],
                cantidad=ingrediente['cantidad']
            )

    # Convertir la hora a la zona horaria local (Santiago) para la respuesta
    #santiago_tz = pytz.timezone('America/Santiago')
    fecha_inicio_local = lista_minuta.fecha_inicio
    fecha_termino_local = lista_minuta.fecha_termino

    # crear lista de estado de dias y guardar en la base de datos con el valor ep
    estado_dias = []
    for minuta in lista_minuta.minutas.all():
        estado_dias.append({
            'id_minuta': minuta.id_minuta,
            'state': 'ep'
        })
    # cargar en bd el estado de los dias
    InfoMinuta.objects.filter(lista_minuta=lista_minuta).update(estado_dias=estado_dias)

    # Formatear las fechas de las minutas para la respuesta
    minutas_data = [
            {
                'type_food': minuta.type_food,
                'name_food': minuta.name_food,
                'fecha': minuta.fecha,
                'ingredientes': [
                    {
                        'nombre': ingrediente.nombre_ingrediente,
                        'tipo_medida': ingrediente.tipo_medida,
                        'cantidad': ingrediente.cantidad
                    } for ingrediente in minuta.ingredientes.all()
                ]
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
    """
    Endpoint for checking if there is an active minuta for the user.
    """

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
            'fecha': minuta.fecha,
            'ingredientes': [
                {   
                    'id_ingrediente': ingrediente.id_minuta_ingrediente,
                    'nombre': ingrediente.nombre_ingrediente,
                    'tipo_medida': ingrediente.tipo_medida,
                    'cantidad': ingrediente.cantidad
                } for ingrediente in minuta.ingredientes.all()
            ]
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
            'cantidad_personas': info_minuta.cantidad_personas,
            'estado_minutas': info_minuta.estado_dias,

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
    """
    Endpoint for deactivating a minuta of alimentos.
    """
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
    """
    Endpoint for getting the history of minutas of alimentos for a user.
    """
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
    """
    Endpoint for getting the recipe of an aliment in a minuta.
    """
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

    
    receta = getreceta(name_minuta, people_number)
    
    return Response({'receta': receta}, status=200)

#Control de uso productos en minuta
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
            name="date",
            required=True,
            location="form",
            schema=coreschema.String(description='Date.')
        ),
        coreapi.Field(
            name="realizado",
            required=True,
            location="form",
            schema=coreschema.String(description='Realizado.')
        ),
    ]
))
def control_uso_productos(request):
    """
    Endpoint for controlling the use of products in a minuta, realize discount if realizado is true else not realize changes.
    """
    user_id = request.data.get('user_id')
    date_str = request.data.get('date')
    realizado = request.data.get('realizado')
    if not all([user_id, date_str, realizado]):
        return Response({'error': 'All fields are required.'}, status=400)

    try:
        user = Users.objects.get(id_user=user_id)
        date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except Users.DoesNotExist:
        return Response({'error': 'User not found.'}, status=404)
    except ValueError:
        return Response({'error': 'Invalid date format. Use YYYY-MM-DD.'}, status=400)

    resultado = obtener_y_validar_minuta_del_dia(user, date, realizado)

    #funcion para actualizar data de objetivos
    control_objetivo_minuta(user,realizado)

    #actualiar info minuta con el estado de los dias
    #traer el estado de los dias
    update_estado_dias(user, date, realizado)
    
    if resultado['status'] == 'error':
        return Response({'status': 'error', 'message': resultado['message']}, status=400)

    return Response({'status': 'success', 'message': resultado['message']}, status=200)


# EDITAR LA CANTIDAD DE INGREDIENTE DE LA MINUTA DEL DIA 
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
            name="date",
            required=True,
            location="form",
            schema=coreschema.String(description='Date.')
        ),
        coreapi.Field(
            name="id_ingrediente",
            required=True,
            location="form",
            schema=coreschema.Integer(description='Ingrediente ID.')
        ),
        coreapi.Field(
            name="cantidad",
            required=True,
            location="form",
            schema=coreschema.Integer(description='Cantidad.')
        ),
    ]
))
def edit_ingrediente_minuta(request):
    """
    Endpoint for editing the quantity of an ingredient in a minuta.
    """
    user_id = request.data.get('user_id')
    date_str = request.data.get('date')
    id_ingrediente = request.data.get('id_ingrediente')
    cantidad = request.data.get('cantidad')

    if not all([user_id, date_str, id_ingrediente, cantidad]):
        return Response({'error': 'All fields are required.'}, status=400)

    try:
        user = Users.objects.get(id_user=user_id)
        date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except Users.DoesNotExist:
        return Response({'error': 'User not found.'}, status=404)
    except ValueError:
        return Response({'error': 'Invalid date format. Use YYYY-MM-DD.'}, status=400)

    resultado = editar_cantidad_ingrediente_minuta(user, date, id_ingrediente, cantidad)

    if resultado['status'] == 'error':
        return Response({'status': 'error', 'message': resultado['message']}, status=400)

    return Response({'status': 'success', 'message': resultado['message']}, status=200)

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
def obtener_notificacion_minuta(request):
    """
    Endpoint for getting the notifications of a user, alert the user when exist minuta or not for example
    1. if exist minuta active generated notification for recorder a user realized minuta.
    2. if not exist minuta active generated notification for recorder a user not realized minuta and may created minuta plan.
    """
    usuario = request.query_params.get('user_id')
    print(usuario)
    mensaje = verificar_estado_minuta(usuario)
    print(mensaje)
    if mensaje:
        return Response ({"notifications": [
            { "notification": mensaje }
        ]}, status=200)
    else:
        return Response({"notifications": [
            { "notification": False }
        ]}, status=200)

    
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
def obtener_notificacion_despensa(request):
    """
    Endpoint for getting the notifications of a user, alert a user in base state despensa for example:
    1.if despensa is not have product and minuta active generte notification for join products for not have prductos for complete minuta.
    2.if despensa is have product generte and have not minuta active notification for generated plan de minutas.
    3.if despensa is not have product and not minuta active generte notification for join products for generated plan de minutas.
    4. if not have check that before condition generte a false notification.
    """
    user_id = request.query_params.get('user_id')
    dispensa_id = request.query_params.get('dispensa_id')
    mensaje = verificar_dispensa(user_id,dispensa_id)
    
    return Response ({"notifications": [
            { "notification": mensaje }
        ]}, status=200)

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
def uso_productos_para_minuta(request):
    """
    Endpoint for getting the notifications of a user, NOT USED NOT USED, you dont ask for why !!!.
    """
    user_id = request.query_params.get('user_id')
    mensaje = verificar_alimentos_minuta(user_id)
    if mensaje:
        return Response ({"notifications": [
            { "notification": mensaje }
        ]}, status=200)
    else:
        return Response({"notifications": [
            { "notification": "No tienes nuevas notificaciones" }
        ]}, status=200)
    
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
def uso_productos_para_despensa(request):
    """
    Endpoint for getting the notifications of a user, this alert exist for 
    generate "notifications" for the user when exist suggestion of use products.
    would response  ¡Tienes sugerencias de uso para los alimentos en tu despensa! if have productos that not use in minuta.
    elif "No hay minuta activa para el usuario, crear una minuta." 
    else "No hay alimentos en la despensa para entregarte una sugerencia." 
    """
    user_id = request.query_params.get('user_id')
    mensaje = notificacion_sugerencia(user_id)
    if mensaje:
        return Response ({"notifications": [
            { "notification": mensaje }
        ]}, status=200)
    else:
        return Response({"notifications": [
            { "notification": "No tienes nuevas notificaciones" }
        ]}, status=200)




#get sugerence of products
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
            name="date",
            required=True,
            location="query",
            schema=coreschema.Integer(description='Dispensa ID.')
        ),
    ]
))
def sugerencia_productos_despensa(request):
    """
    Endpoint for getting the data suggestions of use products that not use in minuta and stay in despensa.
    Have to uses after generate notification for user with notificacion_sugerencia that may be have suggestions.
    """
    user_id = request.query_params.get('user_id')
    date_str = request.query_params.get('date')
    
    if not all([user_id, date_str]):
        return Response({'error': 'User ID and Date are required.'}, status=400)
    
    try:
        user = Users.objects.get(id_user=user_id)
        date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except Users.DoesNotExist:
        return Response({'error': 'User not found.'}, status=404)
    
    # obtener sugerencia 
    suggestion_user = Sugerencias.objects.filter(user=user, fecha=date)
    if suggestion_user:
        suggestion = suggestion_user.first().suggestion
    else:
        suggestion = "No hay sugerencias para el usuario en la fecha indicada."

    return Response({'suggestion': suggestion}, status=200)

# Recomendaciones de compra 
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
            name="type_recommendation",
            required=True,
            location="form",
            schema=coreschema.Integer(description='Type of recommendation. Allowed values: 1, 2, 3. (1: Comida más utilizada, 2: Dieta más utilizada, 3: Uso frecuente por comida.)')
        ),
    ]
))
def recomendacion_compra(request):
    """
    Endpoint for generated recomendation the buy a user based your stadistics, is not notification.
    """
    user_id = request.data.get('user_id')
    type_recommendation = request.data.get('type_recommendation')
    print(f"Received type_recommendation: {type_recommendation}")

    if not all([user_id, type_recommendation]):
        return Response({'error': 'User ID and Type of recommendation are required.'}, status=400)
    try:
        user = Users.objects.get(id_user=user_id)
    except Users.DoesNotExist:
        return Response({'error': 'User not found.'}, status=404)

    try:
        type_recommendation = int(type_recommendation)
    except ValueError:
        return Response({'error': 'Type of recommendation must be an integer.'}, status=400)
    
    #control de data minima para la recomendacion
    data_minima = data_minima_recomendacion_compra(user,type_recommendation)
    if not data_minima or data_minima == "error":
        return Response({'recommendation': 'aun no hay recomendaciones para ti '}, status=500)

    # Switch para rotar entre las recomendaciones
    if type_recommendation == 1:
        recommendation = typo_food_mas_utlizado(user.id_user)
        context = 'el analicis del usuario indica que la comida mas utilizada es: '
    elif type_recommendation == 2:
        recommendation = obtener_dieta_mas_usada(user.id_user)
        context = 'el analicis del usuario indica que la dieta mas utilizada es: '
    elif type_recommendation == 3:
        recommendation = calcular_uso_frecuente_por_comida(user.id_user)
        context = 'el analicis del usuario indica que el los alimentos mas utilizados en los tipo comidas son: '
    else:
        return Response({'error': 'Invalid type of recommendation. Allowed values: 1, 2, 3.'}, status=400)
    
    recomendation_ia = crear_recomendacion_compra(recommendation, context)

    return Response({'recommendation': recomendation_ia}, status=200)

## CREAR OBJETIVOS 
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
            name="id_tipo_objetivo",
            required=True,
            location="form",
            schema=coreschema.Integer(description='Objetivo.')
        ),
        coreapi.Field(
            name="meta_objetivo",
            required=True,
            location="form",
            schema=coreschema.Integer(description='meta del objetivo.')
        ),
    ]
))
def crear_objetivo(request):
    """
    Endpoint for creating a objetive for a user.
    """
    user_id = request.data.get('user_id')
    id_tipo_objetivo = request.data.get('id_tipo_objetivo')
    meta_objetivo = request.data.get('meta_objetivo')

    if not all([user_id, id_tipo_objetivo, meta_objetivo]):
        return Response({'error': 'User ID, Tipo Objetivo and Meta Objetivo are required.'}, status=400)

    try:
        user = Users.objects.get(id_user=user_id)
    except Users.DoesNotExist:
        return Response({'error': 'User not found.'}, status=404)

    try:
        meta_objetivo = int(meta_objetivo)
    except ValueError:
        return Response({'error': 'Meta Objetivo must be an integer.'}, status=400)
    
    try:
        tipo_objetivo = TipoObjetivo.objects.get(id_tipo_objetivo=id_tipo_objetivo)
    except TipoObjetivo.DoesNotExist:
        return Response({'error': 'Tipo Objetivo not found.'}, status=404)
    
    try:
        objetivo = Objetivo.objects.get(user=user, state_objetivo=True)
        return Response({'error': 'User already has an active objective.'}, status=400)
    except Objetivo.DoesNotExist:
        pass
    
    
    try:
        objetivo = Objetivo.objects.create(
            user=user,
            id_tipo_objetivo=tipo_objetivo,
            meta_total=meta_objetivo,
            state_objetivo=True
        )
         # Crear el progreso inicial en 0 para el nuevo objetivo
        ProgresoObjetivo.objects.create(
            objetivo=objetivo,
            progreso_diario=0,
            progreso_acumulado=0
        )

        objetivo_data = ObjetivoSerializer(objetivo).data

        return Response({'message': 'Objetivo created successfully.', 'objetivo': objetivo_data}, status=201)
    except Exception as e:
        return Response({'error': str(e)}, status=500)
    
## CONSULTAR OBJETIVOS
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
def consultar_objetivo(request):
    """
    Endpoint for getting the objetive of a user.
    """
    user_id = request.query_params.get('user_id')

    if not user_id:
        return Response({'error': 'User ID is required.'}, status=400)

    try:
        user = Users.objects.get(id_user=user_id)
    except Users.DoesNotExist:
        return Response({'error': 'User not found.'}, status=404)
    
    try:
        objetivo = Objetivo.objects.get(user=user, state_objetivo=True)
    except Objetivo.DoesNotExist:
        return Response({'error': 'No active objective found for the user.'}, status=404)
    
    objetivo_data = ObjetivoSerializer(objetivo).data

    return Response({'objetivo': objetivo_data}, status=200)

## ELIMINAR OBJETIVOS
@api_view(['PUT'])
@schema(AutoSchema(
    manual_fields=[
        coreapi.Field(
            name="user_id",
            required=True,
            location="form",
            schema=coreschema.Integer(description='User ID.')
        ),
    ]
))
def eliminar_objetivo(request):
    """
    Endpoint for deactivating a objetive of a user.
    """
    user_id = request.data.get('user_id')

    if not user_id:
        return Response({'error': 'User ID is required.'}, status=400)
    
    try:
        user = Users.objects.get(id_user=user_id)
    except Users.DoesNotExist:
        return Response({'error': 'User not found.'}, status=404)
    
    try:
        objetivo = Objetivo.objects.get(user=user, state_objetivo=True)
    except Objetivo.DoesNotExist:
        return Response({'error': 'No active objective found for the user.'}, status=404)
    
    # Cambiar estado del objetivo a inactivo
    objetivo.state_objetivo = False
    objetivo.save()

    # Verificar si el estado se ha actualizado correctamente
    if not objetivo.state_objetivo:
        return Response({'message': 'Objetivo is deactivated.'}, status=200)
    else:
        return Response({'error': 'Failed to deactivate Objetivo.'}, status=500)
    
## CONSULTAR PROGRESO DE OBJETIVOS
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
def consultar_progreso_objetivo(request):
    """
    Endpoint for getting the progress of the objetive of a user.
    """
    user_id = request.query_params.get('user_id')

    if not user_id:
        return Response({'error': 'User ID is required.'}, status=400)

    try:
        user = Users.objects.get(id_user=user_id)
    except Users.DoesNotExist:
        return Response({'error': 'User not found.'}, status=404)
    
    try:
        objetivo = Objetivo.objects.get(user=user, state_objetivo=True)
    except Objetivo.DoesNotExist:
        return Response({'error': 'No active objective found for the user.'}, status=404)
    
    progreso = ProgresoObjetivo.objects.get(objetivo=objetivo)
    progreso_data = ProgresoObjetivoSerializer(progreso).data

    return Response({'progreso': progreso_data}, status=200)