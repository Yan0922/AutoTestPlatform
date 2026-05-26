"""筛选条件."""
import django_filters

from .models import Audio


class CharInFilter(django_filters.BaseInFilter, django_filters.CharFilter):
    """支持 ?language=zh&language=ru 或 ?language=zh,ru 的多选筛选."""


class AudioFilter(django_filters.FilterSet):
    language = CharInFilter(field_name="language", lookup_expr="in")
    source = CharInFilter(field_name="source", lookup_expr="in")
    industry = CharInFilter(field_name="industry", lookup_expr="in")
    noise = CharInFilter(field_name="noise", lookup_expr="in")
    duration_min = django_filters.NumberFilter(field_name="duration", lookup_expr="gte")
    duration_max = django_filters.NumberFilter(field_name="duration", lookup_expr="lte")
    name = django_filters.CharFilter(field_name="name", lookup_expr="icontains")
    dataset_id = django_filters.NumberFilter(method="filter_dataset")

    def filter_dataset(self, queryset, name, value):
        return queryset.filter(datasets__id=value)

    class Meta:
        model = Audio
        fields = [
            "language",
            "source",
            "industry",
            "noise",
            "duration_min",
            "duration_max",
            "name",
            "dataset_id",
        ]
