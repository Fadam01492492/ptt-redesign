from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("boards/", views.board_list, name="board_list"),
    path("bbs/<str:name>/", views.board_detail, name="board_detail"),
    path("bbs/<str:name>/favorite/", views.toggle_favorite, name="toggle_favorite"),
    path("post/<int:pk>/", views.post_detail, name="post_detail"),
    path("post/new/", views.post_create, name="post_create"),
    path("search/", views.search, name="search"),
    path("me/", views.my_favorites, name="my_favorites"),
    path("signup/", views.signup, name="signup"),
]
