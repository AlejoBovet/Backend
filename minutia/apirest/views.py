from rest_framework import viewsets
from rest_framework.decorators import api_view, schema
from rest_framework.response import Response
from rest_framework.schemas import AutoSchema
from .models import Users,Dispensa
from .serializer import UsersSerializer
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

    # Save the PDF file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{user_id}.pdf") as temp_pdf:
        for chunk in pdf_file.chunks():
            temp_pdf.write(chunk)
        temp_pdf_path = temp_pdf.name

    # For now, just return a success response with the temporary file path
    return Response({'message': 'PDF file received successfully.', 'temp_pdf_path': temp_pdf_path}, status=200)