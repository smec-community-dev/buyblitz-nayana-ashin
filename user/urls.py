

from django.contrib import admin
from django.urls import path
from user import views

urlpatterns = [

    path("register/", views.register_user, name="register"),
    path("login/", views.login_user, name="login"),
    path("logout/", views.logout_user, name="logout"),
    # path("profile/", views.profile, name="profile"),
    path("home/",views.home,name="home")

]