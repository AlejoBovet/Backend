import pytz
import os
import re
import json
from datetime import datetime
from dateutil import parser

def process_response(response):
    while True:
        try:
            # Eliminar delimitadores de código si existen
            if response.startswith("```json") and response.endswith("```"):
                response = response[7:-3].strip()
            
            # Intentar parsear la respuesta como JSON
            data = json.loads(response)
            print("Parsed JSON successfully:", data)
            break
        except json.JSONDecodeError:
            print("Failed to parse JSON. Trying as string.")
            try:
                # Intentar manejar la respuesta como una cadena de texto
                data = json.loads(response.replace("'", "\""))
                print("Handled as string successfully:", data)
                break
            except json.JSONDecodeError:
                print("Failed to handle as string. Trying to clean up the response.")
                try:
                    # Intentar limpiar la respuesta y parsearla nuevamente
                    response = response.replace("\n", "").replace("\t", "").strip()
                    data = json.loads(response)
                    print("Cleaned up and parsed JSON successfully:", data)
                    break
                except json.JSONDecodeError:
                    print("Failed to clean up and parse JSON. Trying as plain string.")
                    try:
                        # Intentar manejar la respuesta como una cadena de texto simple
                        data = str(response)
                        print("Handled as plain string successfully:", data)
                        break
                    except Exception as e:
                        print("Failed to handle as plain string:", e)
                        break
        except Exception as e:
            print("An unexpected error occurred:", e)
            break

    return data