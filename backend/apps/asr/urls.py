"""ASR 模块路由."""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    AsrModelViewSet,
    AudioUploadView,
    AudioViewSet,
    DatasetViewSet,
    TestTaskViewSet,
)


router = DefaultRouter()
router.register("models", AsrModelViewSet, basename="asr-model")
router.register("datasets", DatasetViewSet, basename="dataset")
router.register("audios", AudioViewSet, basename="audio")
router.register("tasks", TestTaskViewSet, basename="task")


urlpatterns = [
    path("", include(router.urls)),
    path("upload/audio/", AudioUploadView.as_view(), name="upload-audio"),
]
