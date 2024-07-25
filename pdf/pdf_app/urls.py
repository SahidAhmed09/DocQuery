# urls.py
from django.urls import path
from .views import upload_file, query_file

urlpatterns = [
    path('api/upload/', upload_file, name='upload_file'),
    path('api/query/', query_file, name='query_file'),
]
