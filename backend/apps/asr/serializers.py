"""DRF 序列化器."""
from rest_framework import serializers

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


class AsrModelFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = AsrModelFile
        fields = ["id", "file_name", "file_size", "file_path", "created_at"]


class AsrModelSerializer(serializers.ModelSerializer):
    files = AsrModelFileSerializer(many=True, read_only=True)
    language_display = serializers.CharField(source="get_language_display", read_only=True)
    size_display = serializers.CharField(source="get_size_display", read_only=True)

    class Meta:
        model = AsrModel
        fields = [
            "id",
            "name",
            "language",
            "language_display",
            "version",
            "size",
            "size_display",
            "dir_path",
            "files",
            "status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["dir_path", "status", "created_at", "updated_at"]


class DatasetSerializer(serializers.ModelSerializer):
    language_display = serializers.CharField(source="get_language_display", read_only=True)
    total_audio = serializers.IntegerField(read_only=True)
    total_duration = serializers.FloatField(read_only=True)

    class Meta:
        model = Dataset
        fields = [
            "id",
            "name",
            "language",
            "language_display",
            "total_audio",
            "total_duration",
            "status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["status", "created_at", "updated_at"]


class AudioSerializer(serializers.ModelSerializer):
    dataset_ids = serializers.SerializerMethodField()
    dataset_names = serializers.SerializerMethodField()
    language_display = serializers.CharField(source="get_language_display", read_only=True)
    source_display = serializers.CharField(source="get_source_display", read_only=True)
    noise_display = serializers.CharField(source="get_noise_display", read_only=True)
    industry_display = serializers.CharField(source="get_industry_display", read_only=True)

    class Meta:
        model = Audio
        fields = [
            "id",
            "name",
            "language",
            "language_display",
            "audio_path",
            "source",
            "source_display",
            "noise",
            "noise_display",
            "industry",
            "industry_display",
            "duration",
            "ref_text",
            "dataset_ids",
            "dataset_names",
            "status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["status", "created_at", "updated_at"]

    def get_dataset_ids(self, obj):
        return list(obj.datasets.filter(status=1).values_list("id", flat=True))

    def get_dataset_names(self, obj):
        return list(obj.datasets.filter(status=1).values_list("name", flat=True))


class TestTaskSerializer(serializers.ModelSerializer):
    model_name = serializers.CharField(source="model.name", read_only=True)
    task_status_display = serializers.CharField(source="get_task_status_display", read_only=True)
    list_status = serializers.SerializerMethodField()
    list_status_display = serializers.SerializerMethodField()
    dataset_ids = serializers.SerializerMethodField()
    dataset_names = serializers.SerializerMethodField()

    class Meta:
        model = TestTask
        fields = [
            "id",
            "name",
            "model",
            "model_name",
            "task_status",
            "task_status_display",
            "list_status",
            "list_status_display",
            "dataset_ids",
            "dataset_names",
            "created_at",
            "finished_at",
            "error_message",
        ]
        read_only_fields = [
            "task_status",
            "created_at",
            "finished_at",
            "error_message",
            "list_status",
            "list_status_display",
        ]

    def get_list_status(self, obj):
        from .task_run_group import get_list_display_status

        status, _ = get_list_display_status(obj)
        return status

    def get_list_status_display(self, obj):
        from .task_run_group import get_list_display_status

        _, label = get_list_display_status(obj)
        return label

    def get_dataset_ids(self, obj):
        return list(obj.task_datasets.values_list("dataset_id", flat=True))

    def get_dataset_names(self, obj):
        return list(obj.task_datasets.values_list("dataset__name", flat=True))


class TestTaskDatasetSerializer(serializers.ModelSerializer):
    dataset_name = serializers.CharField(source="dataset.name", read_only=True)

    class Meta:
        model = TestTaskDataset
        fields = [
            "id",
            "dataset",
            "dataset_name",
            "total_audio",
            "total_duration",
            "avg_wer",
            "ret",
            "s_cnt",
            "i_cnt",
            "d_cnt",
            "hit_cnt",
        ]


class TestAudioResultSerializer(serializers.ModelSerializer):
    audio_name = serializers.CharField(source="audio.name", read_only=True)
    audio_path = serializers.CharField(source="audio.audio_path", read_only=True)
    duration = serializers.FloatField(source="audio.duration", read_only=True)

    class Meta:
        model = TestAudioResult
        fields = [
            "id",
            "task",
            "dataset",
            "audio",
            "audio_name",
            "audio_path",
            "duration",
            "ref_text",
            "hyp_text",
            "wer",
            "errors_json",
        ]
