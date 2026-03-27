from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('perfil/', views.perfil_view, name='perfil'),
    path('treinos/', views.treinos_view, name='treinos'),
    path('exercicios/', views.exercicios_view, name='exercicios'),
    path('execucao/', views.execucao_view, name='execucao'),
    path('treinos/excluir/<int:treino_id>/', views.excluir_treino, name='excluir_treino'),
    
]