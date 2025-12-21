from django.urls import path
from . import views


urlpatterns = [
    path("create/", views.create_sr_form, name="create_sr_form"),
    path("create/submit/", views.create_sr_submit, name="create_sr_submit"),
    path("view/<int:sr_id>/", views.view_sr, name="view_sr"),
    path("list_sr/", views.list_sr, name="list_sr"),
    path("view/<int:sr_id>/comment/", views.add_sr_comment, name="add_sr_comment"),
    path("view/<int:sr_id>/close/", views.close_sr, name="close_sr"),

]