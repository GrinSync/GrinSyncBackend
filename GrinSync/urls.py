"""
URL configuration for GrinSync project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
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
from django.urls import include, path
from rest_framework.authtoken import views as tokenViews
from api import views as apiViews

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/search', apiViews.search, name = 'search'),
    path('api/getUser', apiViews.getUser, name = 'getUser'),
    path('api/getEvent', apiViews.getEvent, name = 'getEvent'),
    path('api/getAll', apiViews.getAll, name = 'getAll'),
    path('api/getLikedEvents', apiViews.getlikedEvents, name = 'getLikedEvents'),
    path('api/likeEvent', apiViews.likeEvent, name = 'likeEvent'),
    path('api/upcoming', apiViews.getUpcoming, name = 'getUpcomming'),
    path('api/auth', tokenViews.obtain_auth_token),
    path('auth/', include('django.contrib.auth.urls')),
    path('api/validate/login', apiViews.validateLogin, name = 'vallog'),
    path('api/validate', apiViews.validate, name = 'val'),
    path('api/create/user', apiViews.createUser, name = 'newUser'),
    path('api/create/event', apiViews.createEvent, name = 'newEvent'),
]
