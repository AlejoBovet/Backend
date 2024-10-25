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
    re_path('dispensa_detail/', views.dispensa_detail),
    re_path('create_minuta/', views.create_meinuta),
    re_path('statusminute/', views.active_minuta),
    re_path('minuta_detail/', views.minuta_detail),
    re_path('desactivate_minuta/', views.desactivate_minuta),
    re_path('minuta_history/', views.minuta_history),
    re_path('get_receta/', views.get_receta),
    re_path('notificaciones1/', views.obtener_notificacion),
    re_path('notificaciones2/', views.obtener_notificacion_dispensa)
]