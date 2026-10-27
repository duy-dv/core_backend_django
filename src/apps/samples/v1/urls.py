"""
Đường dẫn CRUD của module mẫu phiên bản 1.
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.samples.v1.views.samples import SampleItemViewSetV1

router = DefaultRouter()
router.register(r"", SampleItemViewSetV1, basename="sample-v1")

urlpatterns = [
    path("", include(router.urls)),
]
