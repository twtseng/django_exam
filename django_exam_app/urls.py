"""login_proj URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from . import views

urlpatterns = [
    path('register_user_api', views.register_user_api),
    path('login_user_api', views.login_user_api),
    path('logout_user_api', views.logout_user_api),
    path('set_user_level_api', views.set_user_level_api),
    path('edit_profile_api', views.edit_profile_api),
    path('update_password_api', views.update_password_api),
    path('add_job_api', views.add_job_api),
    path('update_job_api', views.update_job_api),
    path('', views.signin_view,name='signin_view'),
    path('dashboard', views.dashboard_view, name='dashboard_view'),
    path('jobs/new', views.new_job_view, name='new_job_view'),
    path('jobs/<int:job_id>', views.view_job_view, name='view_job_view'),
    path('jobs/edit/<int:job_id>', views.edit_job_view, name='edit_job_view'),
    path('jobs/remove/<int:job_id>', views.remove_job, name='remove_job'),
    path('jobs/add_job_to_user/<int:job_id>',views.add_job_to_user, name='add_job_to_user'),
    path('jobs/remove_job_from_user/<int:job_id>',views.remove_job_from_user, name='remove_job_from_user'),
    path('users/manage', views.manage_users_view, name='manage_users_view'),
    path('users/new', views.new_user, name='new_user'),
    path('users/delete/<int:user_id>', views.delete_user, name='delete_user'),
    path('users/edit/<int:user_id>', views.edit_user_view, name='edit_user_view'),
]
