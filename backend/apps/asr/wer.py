"""WER 计算与 S/I/D 错误标注工具.

为了不依赖外部模型实际推理，这里提供一个真实的 WER 计算（Levenshtein 编辑距离），
模型推理过程在 tasks.py 中用启发式方法生成 hyp_text 以演示流程。
"""
from __future__ import annotations

from typing import List, Tuple


def _tokenize(text: str) -> List[str]:
    """中英混合文本按字符切分(中文)+按空格切分(英文)."""
    tokens: List[str] = []
    buf = ""
    for ch in text.strip():
        if ch.isspace():
            if buf:
                tokens.append(buf)
                buf = ""
            continue
        if "\u4e00" <= ch <= "\u9fff":
            if buf:
                tokens.append(buf)
                buf = ""
            tokens.append(ch)
        else:
            buf += ch
    if buf:
        tokens.append(buf)
    return tokens


def align(ref: List[str], hyp: List[str]) -> Tuple[int, int, int, int, List[dict]]:
    """对 ref/hyp 做最小编辑距离对齐，返回 S/I/D/H 以及每个 token 的状态."""
    n, m = len(ref), len(hyp)
    dp = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(n + 1):
        dp[i][0] = i
    for j in range(m + 1):
        dp[0][j] = j
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            if ref[i - 1] == hyp[j - 1]:
                dp[i][j] = dp[i - 1][j - 1]
            else:
                dp[i][j] = 1 + min(dp[i - 1][j - 1], dp[i - 1][j], dp[i][j - 1])

    i, j = n, m
    ops: List[dict] = []
    s_cnt = i_cnt = d_cnt = h_cnt = 0
    while i > 0 or j > 0:
        if i > 0 and j > 0 and ref[i - 1] == hyp[j - 1]:
            ops.append({"op": "H", "ref": ref[i - 1], "hyp": hyp[j - 1]})
            h_cnt += 1
            i -= 1
            j -= 1
        elif i > 0 and j > 0 and dp[i][j] == dp[i - 1][j - 1] + 1:
            ops.append({"op": "S", "ref": ref[i - 1], "hyp": hyp[j - 1]})
            s_cnt += 1
            i -= 1
            j -= 1
        elif i > 0 and dp[i][j] == dp[i - 1][j] + 1:
            ops.append({"op": "D", "ref": ref[i - 1], "hyp": ""})
            d_cnt += 1
            i -= 1
        else:
            ops.append({"op": "I", "ref": "", "hyp": hyp[j - 1]})
            i_cnt += 1
            j -= 1
    ops.reverse()
    return s_cnt, i_cnt, d_cnt, h_cnt, ops


def compute_wer(ref_text: str, hyp_text: str) -> dict:
    """计算 WER 与错误细节，返回字典."""
    ref_tokens = _tokenize(ref_text)
    hyp_tokens = _tokenize(hyp_text)
    n = len(ref_tokens)
    if n == 0:
        wer = 0.0 if not hyp_tokens else 1.0
        return {
            "wer": wer,
            "s_cnt": 0,
            "i_cnt": len(hyp_tokens),
            "d_cnt": 0,
            "hit_cnt": 0,
            "n_ref": 0,
            "ops": [{"op": "I", "ref": "", "hyp": t} for t in hyp_tokens],
        }
    s, i, d, h, ops = align(ref_tokens, hyp_tokens)
    wer = (s + i + d) / n
    return {
        "wer": round(wer, 4),
        "s_cnt": s,
        "i_cnt": i,
        "d_cnt": d,
        "hit_cnt": h,
        "n_ref": n,
        "ops": ops,
    }
