from datetime import datetime
from ..models import Dispensa, DispensaAlimento, Alimento, Users, Sugerencias, ListaMinuta, InfoMinuta
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
import os

def analizar_despensa(user_id):
    """
    Analiza la despensa del usuario para verificar si hay productos que no se utilizaron en la minuta activa
    y sugiere usos para los alimentos restantes.

    Args:
        user_id (int): El ID del usuario cuya despensa se va a analizar.

    Returns:
        str: Mensaje indicando si se debe generar una notificación o no.
    """
    try:
        # Obtener el objeto Users
        user = Users.objects.get(id_user=user_id)

        # Verificar si hay una minuta activa
        minuta_activa = ListaMinuta.objects.filter(user=user, state_minuta=True).exists()

        if not minuta_activa:
            #print("No hay minuta activa para el usuario.")
            return False
        
        # Verificar si quedan alimentos en la despensa
        alimentos_dispensa = DispensaAlimento.objects.filter(dispensa=user.dispensa).count()

        #recuperar alimentos que estan es despensa pero no se usaron en la minuta
        alimentos = []
        info_minuta = InfoMinuta.objects.get(lista_minuta=ListaMinuta.objects.get(user=user, state_minuta=True))
        alimentos_usados = info_minuta.alimentos_usados_ids
        for alimento in DispensaAlimento.objects.filter(dispensa=user.dispensa):
            if alimento.alimento.id_alimento not in alimentos_usados:
                alimentos.append(alimento.alimento.name_alimento)

        if alimentos_dispensa == 0 or len(alimentos) == 0:
            #print("No hay alimentos en la despensa.")
            return False


        # Enviar lista de alimentos a la función de sugerencias
        llm = ChatOpenAI(model_name="gpt-3.5-turbo", api_key=os.getenv("OPENAI_API_KEY"))
        template = """
        Tengo una lista de alimentos de la despensa: {alimentos}.
        donde estan los alimentos que me sobraron despues de crear la minuta
        necesito que sugieras recetas que pueda hacer con estos alimentos sobrantes
        """

        prompt = PromptTemplate(
            input_variables=["alimentos"], 
            template=template
        )

        formatted_prompt = prompt.format(alimentos=alimentos)
        print("Prompt Formateado:\n", formatted_prompt)

        llm_response = llm.invoke(formatted_prompt)

        # Obtener el contenido de la respuesta como texto
        texto_sugerencias = llm_response.content.strip()
        print("Respuesta de OpenAI:\n", texto_sugerencias)

        # Guardar la respuesta de texto en la base de datos como una sugerencia
        Sugerencias.objects.create(
            user=user,
            recomendacion=texto_sugerencias,
            fecha=datetime.now().date(),
        )

        return "Hay una recomendación para los productos que no utilizaste en tu minuta"

    except Users.DoesNotExist:
        print(f"Usuario con ID {user_id} no existe.")
        return "No generar notificación"
    except Exception as e:
        print(f"Error al analizar la despensa: {e}")
        return "No generar notificación"
