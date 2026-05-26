"""K2 ASR 测试引擎：从数据池生成 scp/src，调用 model-test 脚本，结果回填 DB."""

from .config import is_k2_available
from .task_runner import execute_k2_test_task

__all__ = ["is_k2_available", "execute_k2_test_task"]
