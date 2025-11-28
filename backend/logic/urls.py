from . import views
from django.urls import path

app_name = 'logic'

urlpatterns =[
    path('',views.get_panchangam,name='get_panchangam'),
    path('planets/',views.get_planet_positions,name='get_planet_positions'),
]