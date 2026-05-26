import re
import sys

import jiwer
# import MeCab
# import ujson
from loguru import logger
from pecab import PeCab
from pythainlp.tokenize import word_tokenize

# pip install jiwer MeCab loguru pythainlp pecab -i https://mirrors.aliyun.com/pypi/simple/     

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
    "zh": {"has_space": False, "supports_tokenization": True},
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
    # mecab_tagger = MeCab.Tagger("-Owakati")

    @staticmethod
    def remove_language_id(sentence: str) -> str:
        return re.sub(r">>.+<<", "", sentence)

    def tokenize(self, sentence: str, lang: str, remove_punc: bool = False) -> str:
        if remove_punc:
            sentence = re.sub(r"[^\w\s]", "", sentence)

        if not LANG_ATTR[lang]["supports_tokenization"]:
            sentence = sentence.lower()
            sentence = " ".join(sentence.split())
            return sentence

        sentence = sentence.replace(" ", "")

        if lang == "ja":
            tmp = " ".join(sentence.split())
            return " ".join(tmp).strip()
        if lang == "zh":
            tmp = " ".join(sentence.split())
            return " ".join(tmp).strip()
        if lang == "ko":
            tmp = self.pecab.morphs(sentence)
            return " ".join(tmp).strip()
        if lang == "th":
            tmp = word_tokenize(sentence, engine="newmm")
            return " ".join(tmp).strip()
        return sentence


def get_pair(rst_path: str) -> dict:
    src_path = rst_path.replace(".rst", ".src")
    result = {}
    
    # 读取.src文件
    with open(src_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                parts = line.split(' ', 1)
                if len(parts) == 2:
                    id_, reference = parts
                    if id_ not in result:
                        result[id_] = {}
                    result[id_]["reference"] = reference

    # 读取.rst文件
    with open(rst_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                parts = line.split(' ', 1)
                if len(parts) == 2:
                    id_, transcription = parts
                    if id_ not in result:
                        result[id_] = {}
                        print(f"warning: {id_} src not found")
                    result[id_]["transcription"] = transcription
    
    return result
        

def get_wer(
    rst_path: str, error_type: str = "auto", language: str = "en"
) -> None:
    language_tokenizer = LanguageTokenizer()
    if error_type == "auto":
        if LANG_ATTR[language]["supports_tokenization"]:
            print(language)
            error_type = "cer"
        else:
            error_type = "wer"
            print(error_type)
    refs = []
    hypos = []
    pairs = get_pair(rst_path=rst_path)
    with open(rst_path.replace(".rst", ".err_detail"), "w", encoding="utf-8") as flog1, open(rst_path.replace(".rst", ".err_record"), "w", encoding="utf-8") as flog2:
        for id, pair in pairs.items():
            reference = pair.get("reference", "")
            transcription = pair.get("transcription", "")

            _reference = language_tokenizer.tokenize(
                reference, language, remove_punc=True
            )
            _transcription = language_tokenizer.tokenize(
                transcription, language, remove_punc=True
            )

            if error_type == "cer":
                out = jiwer.process_characters(reference=_reference, hypothesis=_transcription)
            elif error_type == "wer":
                out = jiwer.process_words(reference=_reference, hypothesis=_transcription)
            else:
                raise NotImplementedError(f"Unsupported error type: {error_type}")

            detail = str(jiwer.visualize_alignment(out))
            flog1.write(f"{detail}\n")

            if error_type == "wer":
                if out.wer > 0.1:
                    flog2.write(f"id: {id}\nsrc: {_reference}\nrst: {_transcription}\n\n")
            elif error_type == "cer":
                if out.cer > 0.1:
                    flog2.write(f"id: {id}\nsrc: {_reference}\nrst: {_transcription}\n\n")
                    
            if not _reference:
                logger.warning(
                    f"Empty reference\n"
                    f"Id: {id}\n"
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

    detail = str(jiwer.visualize_alignment(out))
    with open(rst_path.replace(".rst", ".wer"), "w", encoding="utf-8") as flog:
        flog.write(f"{detail}\n")
        flog.write(f"Substitutions: {out.substitutions}\n")
        flog.write(f"Deletions: {out.deletions}\n")
        flog.write(f"Insertions: {out.insertions}\n")
        if error_type == "wer":
            flog.write(f"WER: {round(out.wer * 100, 2)}%\n")
        elif error_type == "cer":
            flog.write(f"CER: {round(out.cer * 100, 2)}%\n")
    # print(detail)
    insert = out.insertions
    delete = out.deletions
    substitution = out.substitutions
    if error_type == "wer":
        er = round(out.wer * 100, 2)
    elif error_type == "cer":
        er = round(out.cer * 100, 2)
    print(f"{er}%({substitution}/{delete}/{insert})")

    return error_type, er, substitution, delete, insert

if __name__ == "__main__":
    rst_path = sys.argv[1]
    error_type = sys.argv[2] if len(sys.argv) > 2 else "auto"
    language = sys.argv[3] if len(sys.argv) > 3 else "en"
    get_wer(
        rst_path=rst_path,
        error_type=error_type,
        language=language,
    )
