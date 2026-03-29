from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('perfil/', views.perfil_view, name='perfil'),

    path('treinos/', views.treinos_view, name='treinos'),
    path('treinos/editar/<int:treino_id>/', views.editar_treino_view, name='editar_treino'),
    path('treinos/excluir/<int:treino_id>/', views.excluir_treino, name='excluir_treino'),

    path('exercicios/', views.exercicios_view, name='exercicios'),
    path('exercicios/excluir/<int:exercicio_id>/', views.excluir_exercicio, name='excluir_exercicio'),

    path('execucao/', views.execucao_view, name='execucao'),
    path('execucao/<int:execucao_id>/', views.execucao_detalhe_view, name='execucao_detalhe'),
    path('execucao/item/<int:item_id>/concluir/', views.concluir_exercicio_view, name='concluir_exercicio'),
]