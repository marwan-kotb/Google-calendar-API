from django.urls import path

from . import views

app_name = 'L'

urlpatterns = [
    path("", views.index, name="index"),
    path("login", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),
    path("register/<str:type>", views.register, name="register"),
    path("blogs", views.blogs, name="blogs"),
    path("Book/<str:doc>/<str:pat>", views.Book, name="Book"),

]