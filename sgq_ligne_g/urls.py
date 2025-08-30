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
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    # path('', include('frontend.urls')),  # Désactivé - remplacé par frontendv3
    path('', include('frontendv3.urls')),
    # path('', include('livesession.urls')),  # Désactivé - utilise l'ancienne API qui stocke à la racine
    path('catalog/', include('catalog.urls')),
    path('wcm/', include('wcm.urls')),
    path('production/', include('production.urls')),
    path('exporting/', include('exporting.urls')),
    path('planification/', include('planification.urls')),
    path('management/', include('management.urls')),
]

# Servir les fichiers statiques en développement
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
