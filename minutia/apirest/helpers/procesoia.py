from rest_framework.response import Response
from langchain import OpenAI
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
import pytz
import os
import json
from datetime import datetime
from dateutil import parser

openai_key = os.getenv("OPENAI_API_KEY")

# Cargar el modelo de OpenAI
llm = ChatOpenAI(model_name="gpt-3.5-turbo", api_key=openai_key)

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
    Extrae los alimentos, la unidad de medida (kg, gr, lt, ml) y la cantidad en formato JSON de la siguiente manera:
    [
        {{ "producto": "nombre del producto", "unidad": "kg o gr o lt o ml", "cantidad": "cantidad" }}
    ]
    Envía solo el JSON con los alimentos sin texto adicional.
    En caso de que no puedas determinar la unidad de medida, y el producto es sólido, asigna "unidad": "kg"; 
    si es líquido, asigna "unidad": "lt". Evita usar "unidad" como valor de unidad.
    """

    prompt = PromptTemplate(
        input_variables=["extracted_text"], 
        template=template
    )

    formatted_prompt = prompt.format(extracted_text=extracted_text)
    print("Prompt Formateado:\n", formatted_prompt)

    try:
        # Ejecutar el modelo AI para obtener la respuesta
        llm_response = llm(formatted_prompt)  # Invocación correcta según la configuración
        #print("Respuesta del LLM:\n", llm_response)

        # Acceder al contenido del mensaje
        json_content = llm_response.content.strip()
        #print("Contenido JSON:\n", json_content)

        # Parsear la respuesta JSON
        alimentos = json.loads(json_content)
    except AttributeError:
        # Manejo de errores si 'llm_response' no tiene el atributo 'content'
        print("Error: El objeto de respuesta del LLM no tiene el atributo 'content'.")
        raise ValueError('Formato de respuesta inválido desde el modelo AI.')
    except json.JSONDecodeError:
        # Manejo de errores si la respuesta no es JSON válido
        print("Error: Respuesta del LLM no es un JSON válido.")
        raise ValueError('Formato JSON inválido.')
    except Exception as e:
        # Manejo de otros posibles errores
        print(f"Error inesperado en extractdataticket: {e}")
        raise ValueError(str(e))

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

    No modifiques el nombre del producto, la unidad ni la cantidad. Devuelve solo el JSON actualizado con la clave "uso_alimento" correctamente asignada.
    """
    
    prompt = PromptTemplate(
        input_variables=["alimentos_list"], 
        template=template
    )
    
    formatted_prompt = prompt.format(alimentos_list=alimentos_list)
    #print("Prompt Formateado:\n", formatted_prompt)
    
    try:
        # Ejecutar el modelo AI para obtener la respuesta
        llm_response = llm(formatted_prompt)
        #print("Respuesta del LLM:\n", llm_response)
    
        # Acceder al contenido del mensaje
        json_content = llm_response.content.strip()
        #print("Contenido JSON:\n", json_content)
    
        # Parsear la respuesta JSON
        usos = json.loads(json_content)
    except AttributeError:
        # Manejo de errores si 'llm_response' no tiene el atributo 'content'
        print("Error: El objeto de respuesta del LLM no tiene el atributo 'content'.")
        raise ValueError('Formato de respuesta inválido desde el modelo AI.')
    except json.JSONDecodeError:
        # Manejo de errores si la respuesta no es JSON válido
        print("Error: Respuesta del LLM no es un JSON válido.")
        raise ValueError('Formato JSON inválido.')
    except Exception as e:
        # Manejo de otros posibles errores
        print(f"Error inesperado en analyzeusoproductos: {e}")
        raise ValueError(str(e))

    # Validar que los usos tengan valores válidos
    for uso in usos:
        if 'uso_alimento' not in uso or not isinstance(uso['uso_alimento'], str):
            print(f"Error: El campo 'uso_alimento' para el producto {uso.get('producto', 'desconocido')} no es válido.")
            raise ValueError(f"El campo 'uso_alimento' para el producto {uso.get('producto', 'desconocido')} no es válido.")

    return usos