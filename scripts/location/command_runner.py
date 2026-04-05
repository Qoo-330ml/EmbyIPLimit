from __future__ import annotations

import shutil
import subprocess


class CommandRunner:
    def __init__(self, timeout_sec: int = 45):
        self.timeout_sec = timeout_sec

    def run(self, cmd: list[str]) -> str:
        if not cmd:
            raise ValueError('空命令')

        if shutil.which(cmd[0]) is None:
            raise FileNotFoundError(f'命令未找到: {cmd[0]}')

        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=self.timeout_sec,
            check=False,
        )

        if proc.returncode != 0:
            stderr = (proc.stderr or '').strip()
            stdout = (proc.stdout or '').strip()
            detail = stderr or stdout or f'exit={proc.returncode}'
            raise RuntimeError(f"命令执行失败: {' '.join(cmd)} | {detail}")

        return (proc.stdout or '').strip()
