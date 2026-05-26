"""ASR 模块数据模型."""
from django.db import models


LANGUAGE_CHOICES = [
    ("zh", "中"),
    ("en", "英"),
    ("es", "西"),
    ("ja", "日"),
    ("ko", "韩"),
    ("ru", "俄"),
    ("fr", "法"),
    ("de", "德"),
    ("th", "泰"),
    ("it", "意"),
    ("ar", "阿"),
]

MODEL_SIZE_CHOICES = [
    ("base", "base"),
    ("small", "small"),
    ("large", "large"),
]

AUDIO_SOURCE_CHOICES = [
    ("Sota1", "Sota1"),
    ("Sota2", "Sota2"),
    ("Sota3", "Sota3"),
    ("gf", "gf"),
    ("outside", "outside"),
    ("cv15", "cv15"),
    ("30min", "30min"),
]

NOISE_CHOICES = [
    ("quiet", "安静"),
    ("low_mid", "中低"),
    ("mid_high", "中高"),
    ("high", "高噪"),
]

INDUSTRY_CHOICES = [
    ("unknown", "未知"),
    ("economy", "经济"),
    ("finance", "金融"),
    ("medical", "医疗"),
    ("travel", "旅游"),
    ("food", "美食"),
    ("technology", "科技"),
]

TASK_STATUS_CHOICES = [
    (1, "进行中"),
    (2, "运行完成"),
    (3, "失败"),
]


class TimeStampedModel(models.Model):
    """所有表的公共字段."""

    status = models.SmallIntegerField(default=1, verbose_name="状态(1有效 0删除)")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        abstract = True


class AsrModel(TimeStampedModel):
    """ASR 模型表."""

    name = models.CharField(max_length=30, verbose_name="模型名称")
    language = models.CharField(max_length=10, choices=LANGUAGE_CHOICES, default="zh", verbose_name="语种")
    version = models.CharField(max_length=30, verbose_name="模型版本")
    size = models.CharField(max_length=10, choices=MODEL_SIZE_CHOICES, default="base", verbose_name="尺寸")
    dir_path = models.CharField(max_length=500, blank=True, default="", verbose_name="模型文件夹路径")

    class Meta:
        db_table = "asr_model"
        ordering = ["-created_at"]
        verbose_name = "ASR模型"

    def __str__(self) -> str:
        return f"{self.name}-{self.version}"


class AsrModelFile(models.Model):
    """ASR 模型文件表."""

    model = models.ForeignKey(AsrModel, on_delete=models.CASCADE, related_name="files", verbose_name="模型")
    file_name = models.CharField(max_length=255, verbose_name="文件名")
    file_size = models.BigIntegerField(default=0, verbose_name="文件大小(字节)")
    file_path = models.CharField(max_length=500, verbose_name="文件路径")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "asr_model_file"
        verbose_name = "ASR模型文件"


class Dataset(TimeStampedModel):
    """数据集表."""

    name = models.CharField(max_length=30, verbose_name="数据集名称")
    language = models.CharField(max_length=10, choices=LANGUAGE_CHOICES, default="zh", verbose_name="语种")

    class Meta:
        db_table = "dataset"
        ordering = ["-created_at"]
        verbose_name = "数据集"

    def __str__(self) -> str:
        return self.name


class Audio(TimeStampedModel):
    """音频数据池."""

    name = models.CharField(max_length=200, verbose_name="音频名称")
    language = models.CharField(max_length=10, choices=LANGUAGE_CHOICES, default="zh", verbose_name="语种")
    audio_path = models.CharField(max_length=500, verbose_name="音频路径(URL)")
    source = models.CharField(max_length=20, choices=AUDIO_SOURCE_CHOICES, default="outside", verbose_name="音频来源")
    noise = models.CharField(max_length=20, choices=NOISE_CHOICES, default="quiet", verbose_name="噪声")
    industry = models.CharField(max_length=20, choices=INDUSTRY_CHOICES, default="unknown", verbose_name="行业")
    duration = models.FloatField(default=0, verbose_name="时长(秒)")
    ref_text = models.TextField(blank=True, default="", verbose_name="参考文本")

    datasets = models.ManyToManyField(Dataset, through="DatasetAudio", related_name="audios")

    class Meta:
        db_table = "audio"
        ordering = ["-created_at"]
        verbose_name = "音频"

    def __str__(self) -> str:
        return self.name


class DatasetAudio(models.Model):
    """数据集与音频的多对多关联."""

    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE, db_constraint=False)
    audio = models.ForeignKey(Audio, on_delete=models.CASCADE, db_constraint=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "dataset_audio"
        unique_together = ("dataset", "audio")
        verbose_name = "数据集音频关联"


class TestTask(TimeStampedModel):
    """测试任务."""

    name = models.CharField(max_length=30, verbose_name="任务名称")
    model = models.ForeignKey(AsrModel, on_delete=models.PROTECT, related_name="tasks", verbose_name="使用的模型")
    task_status = models.SmallIntegerField(choices=TASK_STATUS_CHOICES, default=1, verbose_name="任务状态")
    finished_at = models.DateTimeField(null=True, blank=True, verbose_name="完成时间")
    error_message = models.TextField(blank=True, default="", verbose_name="错误信息")

    class Meta:
        db_table = "test_task"
        ordering = ["-created_at"]
        verbose_name = "测试任务"


class TestTaskDataset(models.Model):
    """任务-数据集 关联及汇总指标."""

    task = models.ForeignKey(TestTask, on_delete=models.CASCADE, related_name="task_datasets")
    dataset = models.ForeignKey(Dataset, on_delete=models.PROTECT)

    total_audio = models.IntegerField(default=0, verbose_name="音频总数")
    total_duration = models.FloatField(default=0, verbose_name="音频总时长(秒)")
    avg_wer = models.FloatField(default=0, verbose_name="平均WER")
    ret = models.FloatField(default=0, verbose_name="RET")
    s_cnt = models.IntegerField(default=0, verbose_name="替换错误数")
    i_cnt = models.IntegerField(default=0, verbose_name="多识别数")
    d_cnt = models.IntegerField(default=0, verbose_name="漏识别数")
    hit_cnt = models.IntegerField(default=0, verbose_name="命中数")

    class Meta:
        db_table = "test_task_dataset"
        unique_together = ("task", "dataset")
        verbose_name = "任务数据集统计"


class TestAudioResult(models.Model):
    """每条音频的识别结果."""

    task = models.ForeignKey(TestTask, on_delete=models.CASCADE, related_name="audio_results")
    dataset = models.ForeignKey(Dataset, on_delete=models.PROTECT)
    audio = models.ForeignKey(Audio, on_delete=models.PROTECT)

    ref_text = models.TextField(blank=True, default="", verbose_name="参考文本快照")
    hyp_text = models.TextField(blank=True, default="", verbose_name="模型预测文本")
    wer = models.FloatField(default=0, verbose_name="WER")
    errors_json = models.JSONField(default=dict, verbose_name="错误细节(S/I/D等)")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "test_audio_result"
        unique_together = ("task", "dataset", "audio")
        verbose_name = "音频识别结果"
