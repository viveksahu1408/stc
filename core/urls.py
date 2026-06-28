# core/urls.py
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.admin_site_urls if hasattr(admin, 'admin_site_urls') else admin.site.urls),
    path('', include('dashboard.urls')), # Hamara dashboard core route par open hoga
]