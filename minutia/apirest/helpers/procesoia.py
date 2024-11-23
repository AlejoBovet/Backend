from rest_framework.response import Response
from langchain import OpenAI
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from .controljson import process_response
import pytz
import os
import re
import json
from datetime import datetime
from dateutil import parser

openai_key = os.getenv("OPENAI_API_KEY")

# Cargar el modelo de OpenAI
llm = ChatOpenAI(model_name="gpt-4-turbo", api_key=openai_key, temperature=0.2)
#llm = ChatOpenAI(model_name="gpt-3.5-turbo", api_key=openai_key)

# extraccion datos boleta 
def extractdataticket(extracted_text):
    """
    Extrae información de una boleta de supermercado utilizando un modelo AI.

    Args:
        extracted_text (str): Texto extraído de la boleta.

    Returns:
        list: Lista de diccionarios con información de los alimentos extraídos.

    Raises:
        ValueError: Si la respuesta del modelo no es un JSON válido o si 
                    los datos extraídos no son válidos.
    """
    template = """
    Tengo la siguiente boleta de supermercado: '{extracted_text}'.
    El formato del detalle de productos en la boleta es el siguiente:
    Cada línea incluye:
    -Código de producto (numérico).
    -Nombre del producto.
    -algunos pueden tener la cantidad del contenido (por ejemplo, '1 kg').
    -Cantidad del producto (por ejemplo, '8 x' para 8 unidades).
    -Precio unitario del producto en una columna alineada a la derecha.
    -Algunos productos pueden tener líneas adicionales que indican descuentos aplicados."
    Y la tarea que necesito esExtrae los alimentos, la unidad de medida (kg, gr, lt, ml) y la cantidad en formato JSON de la siguiente manera:
    formato de salida:
    [
        {{ "producto": "nombre del producto", "unidad": "kg o gr o lt o ml", "cantidad": "cantidad" }}
    ]
    Instrucciones:
    -Envía solo el JSON con los alimentos sin texto adicional.
    -En caso de que no puedas determinar la unidad de medida, y el producto es sólido, asigna "unidad": "kg"; 
    -si es líquido, asigna "unidad": "lt". Evita usar "unidad" como valor de unidad.
    """

    prompt = PromptTemplate(
        input_variables=["extracted_text"], 
        template=template
    )

    formatted_prompt = prompt.format(extracted_text=extracted_text)
    #print("Prompt Formateado:\n", formatted_prompt)

    llm_response = llm(formatted_prompt)
    
    json_content = llm_response.content.strip()
    print("Contenido de json_content (repr):", repr(json_content))
    alimentos=process_response(json_content)
    
    # Validar que los alimentos tengan valores válidos
    for alimento in alimentos:
        cantidad = alimento.get('cantidad', '').replace('.', '', 1)
        if not cantidad.isdigit():
            #print(f"Error: El valor de cantidad para el producto {alimento.get('producto', 'desconocido')} no es válido.")
            raise ValueError(f"El valor de cantidad para el producto {alimento.get('producto', 'desconocido')} no es válido.")

    return alimentos

# Analizar uso de los pruductos 
def analyzeusoproductos(alimentos_list):
    template = """
    Tengo la siguiente lista de alimentos en formato JSON: {alimentos_list}.
    Para cada producto en esta lista, añade únicamente la clave "uso_alimento", indicando en qué comidas se puede usar el alimento (por ejemplo, "desayuno", "almuerzo", y/o "cena").

    Aquí tienes algunas reglas para la clasificación:
    - Productos como cereales, lácteos, frutas y pan suelen usarse en "desayuno".
    - Carnes, pescados, arroces, pastas y vegetales suelen usarse en "almuerzo" y "cena".
    - Dulces o galletas suelen usarse en "desayuno" o "merienda", pero no en comidas principales como almuerzo o cena.
    - Si tienes dudas sobre un alimento específico, inclúyelo en todas las comidas.

    Formato de salida:
    [
        {{ "producto": "nombre del producto", "unidad": "kg o gr o lt o ml", "cantidad": "cantidad", "uso_alimento": "desayuno, almuerzo, cena" }}
    ]
    Instrucciones
    -No modifiques el nombre del producto, la unidad ni la cantidad. 
    -Devuelve solo el JSON actualizado con la clave "uso_alimento" correctamente asignada.
    """
    
    prompt = PromptTemplate(
        input_variables=["alimentos_list"], 
        template=template
    )
    
    formatted_prompt = prompt.format(alimentos_list=alimentos_list)
    #print("Prompt Formateado:\n", formatted_prompt)
    
    llm_response = llm(formatted_prompt)

    json_content = llm_response.content.strip()

    usos=process_response(json_content)

    # Validar que los usos tengan valores válidos
    for uso in usos:
        if 'uso_alimento' not in uso or not isinstance(uso['uso_alimento'], str):
            print(f"Error: El campo 'uso_alimento' para el producto {uso.get('producto', 'desconocido')} no es válido.")
            raise ValueError(f"El campo 'uso_alimento' para el producto {uso.get('producto', 'desconocido')} no es válido.")

    return usos

# Analicis de vialidad de la minuta
def pre_analicis_minuta(alimentos_list,dietary_preference):
    template = """
    Tengo la siguiente lista de alimentos en formato JSON: {alimentos_list}.
    Necesito analizar la viabilidad de crear una minuta con estos alimentos para una dieta {dietary_preference}.
    
    En caso que sea posible devuelve un mensaje de confirmación, en caso contrario, devuelve un mensaje de error.

    Formato de salida:
    {{"status":"viable"}} o {{"status":"no viable"}}

    instrucciones:
    -No modifiques el nombre del producto, la unidad ni la cantidad.
    -Devuelve solo el mensaje de confirmación o error.
    -No hagas preguntas ni incluyas información adicional.
    -No incluyas información adicional.
    -No hagas preguntas.
    -**Solo entrega el formato de salida solicitado.**
    """

    prompt = PromptTemplate(input_variables=["alimentos_list","dietary_preference"], template=template)
    formatted_prompt = prompt.format(alimentos_list=alimentos_list, dietary_preference=dietary_preference)

    llm_response = llm.invoke(formatted_prompt)
    json_content = llm_response.content.strip()
    print("Contenido de json_content (repr):", repr(json_content))

    status=process_response(json_content)

    return status

    


def makeminuta (alimentos_list,people_number,dietary_preference,type_food,starting_date):
    llm = ChatOpenAI(model_name="gpt-4-turbo", api_key=openai_key)
    template = """
    Tengo la siguiente despensa: {alimentos_list} y necesito crear una minuta  Solo puedes utilizar estos ingredientes.
    **Objetivos principales:**
    1.Necesito una minuta exclusivamente para {type_food} para {people_number} personas, con preferencia {dietary_preference}, comenzando desde {starting_date}.
    2.Las fechas deben ser consecutivas y no deben faltar días. Calcula cuántos días puede durar la minuta en función de la cantidad de alimentos disponible, cantidad de personas y preferencia. Utiliza la cantidad adecuada de ingredientes por día.
    3.Aprovecha al máximo todos los ingredientes disponibles en la despensa para crear platos variados y balanceados.
    4.Responde únicamente en formato JSON. Proporciona la respuesta en el siguiente formato JSON:
    
    Formato de salida:
    {{ "name_food": "nombre del plato",
        "type_food": "type_food",
        "fecha": "YYYY-MM-DD",
         "ingredientes": [
            {{ "nombre": "ingrediente1", "tipo_medida": "medida1" ,"cantidad": "cantidad1" }},
            {{ "nombre": "ingrediente2", "tipo_medida": "medida2" ,"cantidad": "cantidad2" }},
            ...
        ],
        }}
    
    Aquí tienes un ejemplo de cómo esta estructurada la despensa (alimento_list):
    [
        {{ "producto": "arroz", "unidad": "kg", "cantidad": "2" , "uso_alimento": "almuerzo, cena" }},
        {{ "producto": "pollo", "unidad": "kg", "cantidad": "1" , "uso_alimento": "almuerzo, cena" }},
    ]

    **Criterios de planificación:**
    - Cada día debe incluir platos adecuados para {type_food}.
    - *Las cantidades de ingredientes deben calcularse con precisión para aprovecharlos al máximo hasta agotarlos.*
    - Si no hay suficiente variedad de ingredientes, puedes repetir platos.
    - Evita opciones inadecuadas como meriendas o snacks (galletas, crema de cacahuate, etc.) como platos principales.
    **Instrucciones:**
    - No hagas preguntas ni incluyas información adicional
    - Selecciona únicamente los ingredientes más adecuados para {type_food} (por ejemplo, no uses ingredientes de meriendas o almuerzos si solo se solicita desayuno).
    - No incluyas ingredientes de meriendas o almuerzos si solo se solicita desayuno.
    - Respeta estrictamente la preferencia dietética solicitada (por ejemplo, no incluyas carne en un menú vegano). 
    - No uses galletas o crema de cacahuate como comidas principales.
     """

    prompt = PromptTemplate(input_variables=["extracted_text","alimentos_list", "people_number", "dietary_preference", "type_food", "starting_date"], template=template)
    formatted_prompt = prompt.format(alimentos_list=alimentos_list, people_number=people_number, dietary_preference=dietary_preference, type_food=type_food, starting_date=starting_date)
    
    # Cambia el uso de 'llm' para usar 'invoke'
    
    llm_response = llm.invoke(formatted_prompt)
    json_content = llm_response.content.strip()
    #print("Contenido de json_content (repr):", repr(json_content))
    
    minutas=process_response(json_content)
    
    return minutas

def getreceta (name_minuta,people_number):
    llm = ChatOpenAI(model_name="gpt-3.5-turbo", api_key=openai_key)
    # Crear el prompt para la API
    template ="""
    Proporciona la receta {name_minuta} para la cantidad de {people_number} personas. La receta debe ser devuelta en formato JSON, siguiendo esta estructura:

    Formato de salida:
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
    print("Contenido de json_content (repr):", repr(json_content))
    # Parsear la respuesta JSON
    
    receta=process_response(json_content)

    return receta


def analizar_repocision_productos( minutas_list, alimentos_usados_list):
    #minuta_activa_dia = minuta_activa_dia
    alimentos_usados_list = alimentos_usados_list
    minutas_list = minutas_list

    #print("minuta_activa_dia:", minuta_activa_dia)
    llm = ChatOpenAI(model_name="gpt-4-turbo", api_key=openai_key,  temperature=0.2)
    # Crear el prompt para la API
    template = """
    Tengo la siguiente minuta completa con los productos planificados: {alimentos_usados_list}.
    Del día específico, tengo la siguiente minuta activa: {minutas_list} la cual contiene los ingredientes que se planearon usar.
    
    La minuta del día no se realizó, y necesito reponer únicamente los productos de la minuta del día que no se utilizaron.

    Formato de salida:
    [
        {{   
            "id_alimento": "id del alimento a reponer",
            "name_alimento": "nombre del producto",
            "unit_measurement": "kg, gr, lt o ml",
            "load_alimento": "cantidad exacta a reponer",
            "uso_alimento": "desayuno, almuerzo, cena"
        }}
    ]

    Instrucciones:
    - Solo incluye los productos de la minuta del día ({minutas_list}) que debían usarse y no se utilizaron.
    - cruza los nombre de los ingredientes para devolver el id del alimento a reponer
    - no entregues productos que no estaban en la minuta del día.
    - *solo entrega el formato de salida solicitado.*
    - *no hagas preguntas ni incluyas información adicional.*
    """


    prompt = PromptTemplate(input_variables=[ "alimentos_usados_list", "minutas_list"], template=template)
    formatted_prompt = prompt.format(alimentos_usados_list=alimentos_usados_list, minutas_list=minutas_list)
    
    # Cambia el uso de 'llm' para usar 'invoke'
    llm_response = llm.invoke(formatted_prompt)
    #print("Respuesta de OpenAI:", llm_response)
    # recorrer la respuesta y extraer el contenido JSON o lista si esta conetnida en []
    json_content = llm_response.content.strip()
    print("Contenido de json_content (repr):", repr(json_content))
    # Intentar parsear el JSON directamente
    
    alimentos_reponer = process_response(json_content)
        
    return alimentos_reponer

def crear_recomendacion_compra(context,metricas_list):
    metricas_list = metricas_list
    llm = ChatOpenAI(model_name="gpt-4-turbo", api_key=openai_key,  temperature=0.2)
    # Crear el prompt para la API
    template = """
    {context} {metricas_list}.
    Necesito una recomendación de compra segun los analicis que hagas de la metrica que te envio.

    Formato de salida:
    [
        {{"titulo_recomendacion":"title1"}},{{"recomendacion":"recomendacion1"}},{{"recomendacion":"recomendacion2"}},{{"recomendacion":"recomendacion3"}}
    ]

    Instrucciones:
    - realiza un análisis de las métricas de uso de alimentos para determinar qué productos se deben comprar.
    - si puedes generar recomandcios de mas variadas o diferentes productos es un plus.
    - recomienda productos que se puedan encontrar en chile.
    - *solo entrega el formato de salida solicitado.*
    """

    prompt = PromptTemplate(input_variables=[ "metricas_list","context"], template=template)
    formatted_prompt = prompt.format(metricas_list=metricas_list,context=context)
    
    # Cambia el uso de 'llm' para usar 'invoke'
    llm_response = llm.invoke(formatted_prompt)
    #print("Respuesta de OpenAI:", llm_response)
    # recorrer la respuesta y extraer el contenido JSON o lista si esta conetnida en []
    json_content = llm_response.content.strip()
    #print("Contenido de json_content (repr):", repr(json_content))
    
    recomendation = process_response(json_content)

    return recomendation
    
