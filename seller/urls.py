from django.contrib import admin
from django.urls import path
from seller import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('sellerdashboard/',views.sellerdashboard)


]
