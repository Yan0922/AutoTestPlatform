import re
import sys

import jiwer
import MeCab
import ujson
from loguru import logger
from pecab import PeCab
from jiwer import transforms
from whisper_normalizer.english import EnglishTextNormalizer
from nemo_text_processing.text_normalization.normalize import Normalizer
from pythainlp.tokenize import word_tokenize

LANG_ATTR = {
    "en": {"has_space": True, "supports_normalization": True},
    "es": {"has_space": True, "supports_normalization": True},
    "de": {"has_space": True, "supports_normalization": False},
    "fr": {"has_space": True, "supports_normalization": False},
    "it": {"has_space": True, "supports_normalization": False},
    "ru": {"has_space": True, "supports_normalization": False},
    "pt": {"has_space": True, "supports_normalization": False},
    "id": {"has_space": True, "supports_normalization": False},
    "hi": {"has_space": True, "supports_normalization": False},
    "te": {"has_space": True, "supports_normalization": False},
    "ta": {"has_space": True, "supports_normalization": False},
    "ur": {"has_space": True, "supports_normalization": False},
    "ms": {"has_space": True, "supports_normalization": False},
    "no": {"has_space": True, "supports_normalization": False},
    "sv": {"has_space": True, "supports_normalization": False},
    "fi": {"has_space": True, "supports_normalization": False},
    "da": {"has_space": True, "supports_normalization": False},
    "nl": {"has_space": True, "supports_normalization": False},
    "ca": {"has_space": True, "supports_normalization": False},
    "he": {"has_space": True, "supports_normalization": False},
    "el": {"has_space": True, "supports_normalization": False},
    "hu": {"has_space": True, "supports_normalization": False},
    "pl": {"has_space": True, "supports_normalization": False},
    "cs": {"has_space": True, "supports_normalization": False},
    "sk": {"has_space": True, "supports_normalization": False},
    "ro": {"has_space": True, "supports_normalization": False},
    "sl": {"has_space": True, "supports_normalization": False},
    "hr": {"has_space": True, "supports_normalization": False},
    "bg": {"has_space": True, "supports_normalization": False},
    "tr": {"has_space": True, "supports_normalization": False},
    "uk": {"has_space": True, "supports_normalization": False},
    "is": {"has_space": True, "supports_normalization": False},
    "sw": {"has_space": True, "supports_normalization": False},
    "zh-cn": {"has_space": False, "supports_normalization": False},
    "ja": {"has_space": False, "supports_normalization": False},
    "ko": {"has_space": False, "supports_normalization": False},
    "th": {"has_space": False, "supports_normalization": False},
    "vi": {"has_space": False, "supports_normalization": False},
    "mn": {"has_space": False, "supports_normalization": False},
    "fa": {"has_space": False, "supports_normalization": False},
    "kk": {"has_space": False, "supports_normalization": False},
    "uz": {"has_space": False, "supports_normalization": False},
    "ar": {"has_space": True, "supports_normalization": False},
    "fil": {"has_space": False, "supports_normalization": False},
}

MAP = {
    # —— 时间标记（am/pm）变体 ——
    "a  m": "am",
    "a m": "am",
    "a.m.": "am",
    "a. m.": "am",
    "am.": "am",
    "p.m.": "pm",
    "p. m.": "pm",
    "pm.": "pm",

    # —— 噪声/占位符（如转写中的星号等）——
    "*": "",
    "***": "",

    # —— 常见连写/断写/合写规范化（以连字符或规范拼写为准）——
    "follow up": "follow-up",
    "followup": "follow-up",
    "no show": "no-show",
    "noshow": "no-show",
    "walk in": "walk-in",
    "walkin": "walk-in",
    "on site": "on-site",
    "onsite": "on-site",
    "in house": "in-house",
    "inhouse": "in-house",
    "last minute": "last-minute",
    "lastminute": "last-minute",
    "non refundable": "non-refundable",
    "nonrefundable": "non-refundable",
    "no smoking": "no-smoking",
    "nosmoking": "no-smoking",
    "wi fi": "wi-fi",
    "wifi": "wi-fi",
    "e mail": "email",
    "e-mail": "email",
    "pre paid": "pre-paid",
    # 你已将 preorder → pre-order，这里补上另一种写法
    "pre-paid": "pre-paid",

    # 自助/前台等领域常见词形
    "self check in": "self-check-in",
    "self check-in": "self-check-in",
    "self checkin": "self-check-in",
    "self-checkin": "self-check-in",

    # 重新安排/升级等（用更常见的规范拼写）
    "re schedule": "reschedule",
    "re-schedule": "reschedule",
    "up grade": "upgrade",

    # o'clock 变体
    "o clock": "oclock",
    "o' clock": "oclock",
    "o'clock": "oclock",

    # —— 常见缩写（去撇号版）——
    # be 动词 + not
    "is not": "isnt",
    "are not": "arent",
    "was not": "wasnt",
    "were not": "werent",

    # 助动词/情态动词 + not
    "do not": "dont",
    "does not": "doesnt",
    "did not": "didnt",
    "have not": "havent",
    "has not": "hasnt",
    "had not": "hadnt",
    "should not": "shouldnt",
    "would not": "wouldnt",
    "could not": "couldnt",
    "will not": "wont",
    "can not": "cannot",  # 保留为 cannot（不强行映射到 cant 以免过激）

    # 主语 + be/助动词
    "you are": "youre",
    "we are": "were",       # 按你的“去撇号”规范，会与过去式同形；如介意可删除此条
    "they are": "theyre",
    "it is": "its",
    "that is": "thats",
    "what is": "whats",
    "who is": "whos",
    "where is": "wheres",
    "when is": "whens",
    "why is": "whys",
    "here is": "heres",
    # 你已包含 there is/there are
    "let us": "lets",

    # 主语 + will/would/have/had
    "i will": "ill",
    "you will": "youll",
    "we will": "well",      # 与单词 well 同形；如介意可删除
    "they will": "theyll",
    "it will": "itll",
    "i would": "id",
    "you would": "youd",
    "we would": "wed",      # 与星期三/动词 wed 同形；如介意可删除
    "they would": "theyd",
    "it would": "itd",
    "i have": "ive",
    "you have": "youve",
    "we have": "weve",
    "they have": "theyve",
    "it has": "its",        # 与 it is 同形，符合去撇号规范
    "i had": "id",
    "you had": "youd",
    "we had": "wed",
    "they had": "theyd",
}


class ReplaceByMap:
    def __init__(self, mapping): self.mapping = mapping
    def __call__(self, s: str) -> str:
        out = s.lower()
        for k, v in self.mapping.items():
            out = out.replace(k, v)
        return " ".join(out.split())  # 折叠多空格

class EnglishNormalizer:
    def __init__(self) -> None:
        self.map = transforms.Compose([
            ReplaceByMap(MAP),
        ])
        self.english_normalizer = EnglishTextNormalizer()
    def __call__(self, text: str) -> str:
        text = self.map(text)
        text = self.english_normalizer(text)
        return text

class LanguageTokenizer:
    pecab = PeCab()
    mecab_tagger = MeCab.Tagger("-Owakati")
    en_normalizer = EnglishNormalizer()
    es_normalizer = Normalizer(
        lang="es",
        input_case="cased",
        cache_dir="./ntp_cache",
        deterministic=True
        )

    @staticmethod
    def remove_language_id(sentence: str) -> str:
        return re.sub(r">>.+<<", "", sentence)

    def tokenize(self, sentence: str, lang: str, remove_punc: bool = False) -> str:
        if remove_punc:
            sentence = re.sub(r"[^\w\s]", "", sentence)

        if LANG_ATTR[lang]["has_space"]:
            sentence = sentence.lower()
            sentence = " ".join(sentence.split())
        else:
            sentence = " ".join(sentence.replace(" ", ""))

        if not LANG_ATTR[lang]["supports_normalization"]:
            return sentence

        if lang == "en":
            return self.en_normalizer(sentence).strip()
        elif lang == "es":
            return self.es_normalizer.normalize(text=sentence, verbose=False)
        else:
            logger.warning(f"Language {lang} not support normalization yet.")
        return sentence


def read_norm(jsonl_path: str, transcription_key: str, error_type: str) -> tuple[list, list, str]:
    """
    Read the normalization file and return a dictionary.
    """
    language_tokenizer = LanguageTokenizer()
    refs = []
    hypos = []
    with open(jsonl_path, "r", encoding="utf-8") as fin:
        for line in fin:
            item = ujson.loads(line)
            if not item:
                continue
            results = item.get("result")
            references = item.get("reference")
            src_lang = item.get("src_lang", transcription_key)

            if src_lang not in LANG_ATTR:
                logger.warning(f"Unsupported language: {src_lang}. Skipping...")
                continue

            if error_type == "auto":
                if LANG_ATTR[src_lang]["supports_normalization"]:
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
            # if not reference or not transcription:
            #     continue

            _reference = language_tokenizer.tokenize(
                reference, src_lang, remove_punc=True
            )
            _transcription = language_tokenizer.tokenize(
                transcription, src_lang, remove_punc=True
            )
            if not _reference:
                logger.warning(
                    f"Empty reference\n"
                    f"Transcription: {transcription}\n"
                    f"Reference: {reference}\n"
                )
                # continue
            refs.append(_reference)
            hypos.append(_transcription)
    return refs, hypos, error_type

def compute_er(refs: list, hypos: list) -> jiwer.CharacterOutput | jiwer.WordOutput:
    """
    Compute the error rate (WER or CER) between references and hypotheses.
    """
    out = jiwer.process_words(reference=refs, hypothesis=hypos)
    return out

def post_process(
    result_path: str,
    jiwer_out: jiwer.CharacterOutput | jiwer.WordOutput,
):
    """
    Post-process the alignment output to get a detailed string representation.
    """
    detail = str(jiwer.visualize_alignment(jiwer_out))
    er = round(jiwer_out.wer * 100, 2) if isinstance(jiwer_out, jiwer.WordOutput) else round(jiwer_out.cer * 100, 2)
    save_path = result_path.replace(".jsonl", ".wer")
    with open(save_path, "w", encoding="utf-8") as flog:
        flog.write(f"{detail}\n")
        flog.write(f"Substitutions: {jiwer_out.substitutions}\n")
        flog.write(f"Deletions: {jiwer_out.deletions}\n")
        flog.write(f"Insertions: {jiwer_out.insertions}\n")
        flog.write(f"WER: {er}%\n")

    insert = jiwer_out.insertions
    delete = jiwer_out.deletions
    substitution = jiwer_out.substitutions

    logger.success(f"Saved to: {save_path}")
    logger.success(f"{er}%({substitution}/{delete}/{insert})")
    return er, substitution, delete, insert

def get_wer(
    result_path: str, error_type: str = "auto", transcription_key: str = "transcription"
) -> tuple:
    refs, hypos, error_type = read_norm(
        jsonl_path=result_path,
        transcription_key=transcription_key,
        error_type=error_type
        )

    out = compute_er(
        refs=refs,
        hypos=hypos,
        )

    er, substitution, delete, insert = post_process(
        result_path=result_path,
        jiwer_out=out
        )

    return error_type, er, substitution, delete, insert


if __name__ == "__main__":
    result_path = "/home/guojun/workspace/k2_asr_model_test/asr_test_code/test_data/test_result/0916_base_outside/es.jsonl"
    transcription_key = "es"
    error_type = "auto"
    get_wer(
        result_path=result_path,
        error_type=error_type,
        transcription_key=transcription_key,
    )