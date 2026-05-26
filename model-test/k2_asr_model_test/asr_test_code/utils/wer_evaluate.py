import jiwer
import ujson
import json
import sys
from loguru import logger
import re

import jieba
import MeCab
from pecab import PeCab
from pythainlp.tokenize import word_tokenize

LANG_ATTR = {
    "en": {"has_space": True, "supports_tokenization": False},
    "es": {"has_space": True, "supports_tokenization": False},
    "de": {"has_space": True, "supports_tokenization": False},
    "fr": {"has_space": True, "supports_tokenization": False},
    "it": {"has_space": True, "supports_tokenization": False},
    "ru": {"has_space": True, "supports_tokenization": False},
    "pt": {"has_space": True, "supports_tokenization": False},
    "id": {"has_space": True, "supports_tokenization": False},
    "hi": {"has_space": True, "supports_tokenization": False},
    "te": {"has_space": True, "supports_tokenization": False},
    "ta": {"has_space": True, "supports_tokenization": False},
    "ur": {"has_space": True, "supports_tokenization": False},
    "ms": {"has_space": True, "supports_tokenization": False},
    "no": {"has_space": True, "supports_tokenization": False},
    "sv": {"has_space": True, "supports_tokenization": False},
    "fi": {"has_space": True, "supports_tokenization": False},
    "da": {"has_space": True, "supports_tokenization": False},
    "nl": {"has_space": True, "supports_tokenization": False},
    "ca": {"has_space": True, "supports_tokenization": False},
    "he": {"has_space": True, "supports_tokenization": False},
    "el": {"has_space": True, "supports_tokenization": False},
    "hu": {"has_space": True, "supports_tokenization": False},
    "pl": {"has_space": True, "supports_tokenization": False},
    "cs": {"has_space": True, "supports_tokenization": False},
    "sk": {"has_space": True, "supports_tokenization": False},
    "ro": {"has_space": True, "supports_tokenization": False},
    "sl": {"has_space": True, "supports_tokenization": False},
    "hr": {"has_space": True, "supports_tokenization": False},
    "bg": {"has_space": True, "supports_tokenization": False},
    "tr": {"has_space": True, "supports_tokenization": False},
    "uk": {"has_space": True, "supports_tokenization": False},
    "is": {"has_space": True, "supports_tokenization": False},
    "sw": {"has_space": True, "supports_tokenization": False},
    "zh-cn": {"has_space": False, "supports_tokenization": True},
    "ja": {"has_space": False, "supports_tokenization": True},
    "ko": {"has_space": False, "supports_tokenization": True},
    "th": {"has_space": False, "supports_tokenization": True},
    "vi": {"has_space": False, "supports_tokenization": False},
    "mn": {"has_space": False, "supports_tokenization": False},
    "fa": {"has_space": False, "supports_tokenization": False},
    "kk": {"has_space": False, "supports_tokenization": False},
    "uz": {"has_space": False, "supports_tokenization": False},
    "ar": {"has_space": False, "supports_tokenization": False},
    "fil": {"has_space": False, "supports_tokenization": False},
}
class LanguageTokenizer:
    # 类变量，避免重复加载
    pecab = PeCab()
    mecab_tagger = MeCab.Tagger("-Owakati")

    @staticmethod
    def remove_language_id(sentence: str) -> str:
        return re.sub(r">>.+<<", "", sentence)

    def tokenize(
        self, 
        sentence: str, 
        lang: str, 
        remove_punc: bool = False
    ) -> str:
        if remove_punc:
            sentence = re.sub(r"[^\w\s]", "", sentence)

        if not LANG_ATTR[lang]["supports_tokenization"]:
            sentence = sentence.lower()
            sentence = " ".join(sentence.split())
            return sentence

        sentence = sentence.replace(" ", "")
        
        if lang == "ja":
            return self.mecab_tagger.parse(sentence).strip()
        if lang == "zh-cn":
            tmp = jieba.cut(sentence)
            return " ".join(tmp).strip()
        if lang == "ko":
            tmp = self.pecab.morphs(sentence)
            return " ".join(tmp).strip()
        if lang == "th":
            tmp = word_tokenize(sentence, engine="newmm")
            return " ".join(tmp).strip()
        return sentence


def get_cer_wer(result_path: str, error_type: str = "auto", transcription_key: str = "transcription") -> None:
    language_tokenizer = LanguageTokenizer()
    refs = []
    hypos = []
    with open(result_path, "r", encoding='utf-8') as fin:
        for line in fin:
            item = ujson.loads(line)
            results = item.get("result")
            references = item.get("reference")
            src_lang = item.get("src_lang", transcription_key)

            if src_lang not in LANG_ATTR:
                logger.warning(f"Unsupported language: {src_lang}. Skipping...")
                continue

            if error_type == "auto":
                if LANG_ATTR[src_lang]["supports_tokenization"]:
                    print(src_lang)
                    error_type = "cer"
                else:
                    error_type = "wer"
                    print(error_type)

            transcription = results.get(transcription_key, "")
            if isinstance(references, dict):
                reference = references.get(transcription_key, "")
            else:
                reference = references
            if not reference:
                continue

            _reference = language_tokenizer.tokenize(
                reference, 
                src_lang, 
                remove_punc=True
                )
            _transcription = language_tokenizer.tokenize(
                transcription, 
                src_lang, 
                remove_punc=True
                )
            if not _reference:
                logger.warning(
                    f"Empty reference\n"
                    f"Transcription: {transcription}\n"
                    f"Reference: {reference}\n"
                    )
                continue
            refs.append(_reference)
            hypos.append(_transcription)

    if error_type == "cer":
        out = jiwer.process_characters(reference=refs, hypothesis=hypos)
    elif error_type == "wer":
        out = jiwer.process_words(reference=refs, hypothesis=hypos)
    else:
        raise NotImplementedError(f"Unsupported error type: {error_type}")

    print(jiwer.visualize_alignment(out))
    insert = out.insertions
    delete = out.deletions
    substitution = out.substitutions
    if error_type == "wer":
        wer = round(out.wer * 100, 2)
        print(f"{wer}%({substitution}/{delete}/{insert})")
    elif error_type == "cer":
        cer = round(out.cer * 100, 2)
        print(f"{cer}%({substitution}/{delete}/{insert})")

def rewrite_ref(ref_path,result_path,src_lang=None):
    rewhite_result_path = ref_path.replace('ref','result')
    with open(rewhite_result_path, "w", encoding="utf-8") as rewhite_result_f:
        with open(result_path, "r", encoding='utf-8') as src_result_f:
            src_result_data = src_result_f.readlines()
        with open(ref_path, "r", encoding='utf-8') as ref_f:
            src_ref_data = ref_f.readlines()
        for i in src_ref_data:
            item = ujson.loads(i)
            ref_name = item.get('name')
            for j in src_result_data:
                split_pcm = j.split(".pcm: ")
                src_result_name = split_pcm[0].split('/')[-1]+".pcm"
                if ref_name == src_result_name:
                    # print(ref_name)
                    # print(split_pcm[-1].strip())
                    # print("**reference**")
                    # print(item.get('reference'))

                    # print("--------------------------------------------------------------")
                    # print(ref_name,split_pcm[-1])
                    item["result"][src_lang] = split_pcm[-1]
                    rewhite_result_f.write(json.dumps(item, ensure_ascii=False) + "\n")
                    break

    return rewhite_result_path

