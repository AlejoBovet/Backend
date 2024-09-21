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
]