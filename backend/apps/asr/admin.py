from django.contrib import admin

from .models import (
    Audio,
    AsrModel,
    AsrModelFile,
    Dataset,
    DatasetAudio,
    TestAudioResult,
    TestTask,
    TestTaskDataset,
)


@admin.register(AsrModel)
class AsrModelAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "language", "version", "size", "status", "created_at")
    search_fields = ("name", "version")


@admin.register(Dataset)
class DatasetAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "language", "status", "created_at")
    search_fields = ("name",)


@admin.register(Audio)
class AudioAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "language", "source", "noise", "industry", "duration", "status")
    search_fields = ("name",)
    list_filter = ("language", "source", "noise", "industry")


@admin.register(TestTask)
class TestTaskAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "model", "task_status", "created_at", "finished_at")


admin.site.register([AsrModelFile, DatasetAudio, TestTaskDataset, TestAudioResult])
