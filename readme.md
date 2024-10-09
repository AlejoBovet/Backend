## Descripcion
Servicio RestApi de la aplicacion MinutIA para Proyecto Capstone DuocUc2024.
## Instalacion 
1. Instalar todas las depencias necesarioas (python y mysql).
2. crear ambiente con "python -m venv nombre_del_entorno" en terminal o powershell
3. activar ambiente (debe ser la version indicada)
4. Intalar las librerias desde requirements.txt 
5. crear arquivo ".env" y cargar credenciales para BD y api
6. actualizar rutas de credenciuales de servicio api en views.py
7. ejecutar python manage.py migrate
8. correr el proyecto
## Uso
La documentacion de los endpoint se encontraran documentados en el subfijo de la ruta '/docs'
ejemplo: http://localhost:9999/docs
## Tecnologias
- Python 3.12.2
- Mysql 8.0.39
