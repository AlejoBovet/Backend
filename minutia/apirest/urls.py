from django.urls import path, include, re_path
from rest_framework import routers
from apirest import views

router = routers.DefaultRouter()
#router.register(r'users', views.UsersViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    re_path('register/', views.register),
    re_path('getinto_ticket/', views.getinto_ticket),
    re_path('join_aliment/', views.join_aliment),
    re_path('delete_alimento/', views.delete_alimento),
    re_path('edit_alimento/', views.edit_alimento),
    re_path('delete_all_alimentos/', views.delete_all_alimentos),
    re_path('dispensa_detail/', views.despensa_detail),
    re_path('status_despensa/', views.status_despensa),
    re_path('create_minuta/', views.create_meinuta),
    re_path('statusminute/', views.active_minuta),
    re_path('minuta_detail/', views.minuta_detail),
    re_path('desactivate_minuta/', views.desactivate_minuta),
    re_path('minuta_history/', views.minuta_history),
    re_path('get_receta/', views.get_receta),
    re_path('edit_productos_minuta_diaria/', views.edit_ingrediente_minuta),
    re_path('notificaciones1_minuta/', views.obtener_notificacion_minuta),
    re_path('notificaciones2_despensa/', views.obtener_notificacion_despensa),
    re_path('notificaciones3_outoff/', views.uso_productos_para_minuta),
    re_path('notificaciones4_aviso_sugerencia/', views.uso_productos_para_despensa),
    re_path('contol_minuta/', views.control_uso_productos),
    re_path('sugerencia_de_uso/', views.sugerencia_productos_despensa),
    re_path('recomendacion_compra/', views.recomendacion_compra),
    re_path('crear_objetivo/', views.crear_objetivo),
    re_path('consultar_objetivo/', views.consultar_objetivo),
    re_path('eliminar_objetivo/', views.eliminar_objetivo),
    re_path("consultar_progreso_objetivo/", views.consultar_progreso_objetivo),
    re_path("estadisticas/", views.estadisticas_usuario),
]