from django.contrib import admin
from django.urls import path

from inquiries import views

handler404 = "inquiries.views.not_found"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", views.home, name="home"),
    path("thanks/<str:reference>/", views.thank_you, name="thank_you"),
    path("track/", views.track, name="track"),
    path("manage/", views.dashboard, name="dashboard"),
    path("manage/export.csv", views.export_csv, name="export_csv"),
    path("manage/<int:pk>/", views.inquiry_detail, name="inquiry_detail"),
]
