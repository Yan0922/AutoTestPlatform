"""平台语种 code 与 K2 测试脚本语种约定映射."""

from __future__ import annotations

# 平台 audio.language -> K2 scp 文件名中的语种（如 zh-cn.scp）
PLATFORM_TO_K2_SCP_LANG: dict[str, str] = {
    "zh": "zh-cn",
    "en": "en",
    "es": "es",
    "ja": "ja",
    "ko": "ko",
    "th": "th",
    "fr": "fr",
    "de": "de",
    "it": "it",
    "ar": "ar",
    "ru": "ru",
}

# K2 scp 语种 -> .src 文件名（test_cases_mutil_thread 中 zh-cn 用 zh.src）
K2_SCP_LANG_TO_SRC_BASENAME: dict[str, str] = {
    "zh-cn": "zh",
    "en": "en",
    "es": "es",
    "ja": "ja",
    "ko": "ko",
    "th": "th",
    "fr": "fr",
    "de": "de",
    "it": "it",
    "ar": "ar",
    "ru": "ru",
}

# jsonl result 里 result 字段的 key
K2_SCP_LANG_TO_RESULT_KEY: dict[str, str] = {
    "zh-cn": "zh-cn",
    "en": "en",
    "es": "es",
    "ja": "ja",
    "ko": "ko",
    "th": "th",
    "fr": "fr",
    "de": "de",
    "it": "it",
    "ar": "ar",
    "ru": "ru",
}


def platform_lang_to_k2_scp_lang(platform_lang: str) -> str:
    lang = (platform_lang or "zh").strip()
    return PLATFORM_TO_K2_SCP_LANG.get(lang, lang)


def k2_src_filename(k2_scp_lang: str) -> str:
    base = K2_SCP_LANG_TO_SRC_BASENAME.get(k2_scp_lang, k2_scp_lang)
    return f"{base}.src"


def k2_scp_filename(k2_scp_lang: str) -> str:
    return f"{k2_scp_lang}.scp"


def k2_result_key(k2_scp_lang: str) -> str:
    return K2_SCP_LANG_TO_RESULT_KEY.get(k2_scp_lang, k2_scp_lang)
