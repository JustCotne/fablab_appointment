"""
URL configuration for appointment project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
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
from django.conf.urls import handler404
from django.conf.urls import handler500


handler500 = 'appointment_app.views.custom_500'
handler404= 'appointment_app.views.custom_404_view'

urlpatterns = [
    path('admin-9d8f7h3g2r8a1t6z0k9u7v9xw/', admin.site.urls),
    path('', include('appointment_app.urls'))
]

