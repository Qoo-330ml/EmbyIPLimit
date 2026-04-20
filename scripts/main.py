from __future__ import annotations

import argparse
import importlib
import shutil
from typing import Iterable

from app_factory import create_app
from config_loader import load_config
from logger import setup_logging, info, error
from network.http_session import update_proxy_config


def _check_python_packages(packages: Iterable[str]) -> list[str]:
    errors: list[str] = []
    for package in packages:
        try:
            importlib.import_module(package)
        except Exception as exc:
            errors.append(f'Python 包缺失/不可用: {package} ({exc})')
    return errors


def _check_cli_commands(commands: Iterable[str]) -> list[str]:
    errors: list[str] = []
    for cmd in commands:
        if shutil.which(cmd) is None:
            errors.append(f'CLI 命令缺失: {cmd}')
    return errors


def run_startup_self_check() -> bool:
    info('🔎 启动自检中...')

    errors: list[str] = []
    errors.extend(
        _check_python_packages(
            [
                'requests',
                'flask',
                'yaml',
                'werkzeug',
                'flask_login',
                'waitress',
            ]
        )
    )
    # 跳过 qoo-ip138 命令检查，因为它可能在 Python 脚本目录中
    # errors.extend(_check_cli_commands(['qoo-ip138']))

    if errors:
        error('❌ 启动自检失败：')
        for item in errors:
            error(f'  - {item}')
        return False

    info('✅ 启动自检通过')
    return True


def main() -> int:
    setup_logging()

    parser = argparse.ArgumentParser(description='EmbyQ')
    parser.add_argument('--self-check', action='store_true', help='仅执行启动自检并退出')
    args = parser.parse_args()

    try:
        config = load_config()
        update_proxy_config(config.get('proxy', {}))
    except Exception as exc:
        error(f'❌ 配置加载失败: {exc}')
        return 1

    if not run_startup_self_check():
        return 1

    if args.self_check:
        return 0

    app = create_app(config)
    app.start()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
