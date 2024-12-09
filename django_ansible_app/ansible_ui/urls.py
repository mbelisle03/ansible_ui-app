from django.contrib.auth import views as auth_views
from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('playbooks/', views.playbook_list, name='playbook_list'),
    path('inventories/', views.inventory_list, name='inventory_list'),
    path('inventories/upload/', views.inventory_upload, name='inventory_upload'),
    path('jobs/', views.job_list, name='jobs_list'),
    path('jobs/create/', views.create_job, name='create_job'),
    path('jobs/<int:job_id>/execute/', views.execute_job, name='execute_job'),
   # path('jobs/execute/<int:job_id>/', views.execute_job, name='execute_job'),
    path('jobs/<int:job_id>/', views.job_detail, name='job_detail'),
    path('playbooks/upload/', views.playbook_upload, name='playbook_upload'),
    path('playbooks/edit/<int:playbook_id>/', views.edit_playbook, name='playbook_edit'),
     # Authentication URLs
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
]
