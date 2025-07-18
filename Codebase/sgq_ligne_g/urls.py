"""
URL configuration for sgq_ligne_g project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
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
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', RedirectView.as_view(url='/frontend/', permanent=False)),
    path('production/', include('production.urls')),
    path('core/', include('core.urls')),
    path('quality/', include('quality.urls')),
    path('frontend/', include('frontend.urls')),
    path('livesession/', include('livesession.urls')),
    path('wcm/', include('wcm.urls')),
    path('reporting/', include('reporting.urls')),
]
