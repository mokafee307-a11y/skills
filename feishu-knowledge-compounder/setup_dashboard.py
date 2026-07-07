#!/usr/bin/env python3
"""
完整自动配置脚本 - 一键创建仪表盘
"""

import os
import sys
import subprocess
from pathlib import Path

def run_script(script_path, description):
    """运行配置脚本"""
    print(f"\n{'='*60}")
    print(f"📍 {description}")
    print('='*60)

    try:
        result = subprocess.run(
            [sys.executable, script_path],
            cwd=Path(script_path).parent,
            capture_output=False
        )
        return result.returncode == 0
    except Exception as e:
        print(f"❌ 执行失败: {e}")
        return False

def main():
    print("\n" + "="*60)
    print("🚀 飞书知识沉淀管理仪表盘 - 完整自动配置")
    print("="*60)

    skill_root = Path('/Users/mokafee/.codex/skills/feishu-knowledge-compounder')

    scripts = [
        ('create_dashboard.py', '第1步: 创建表和字段'),
        ('create_views.py', '第2步: 创建视图'),
    ]

    for script, desc in scripts:
        script_path = skill_root / script
        if not script_path.exists():
            print(f"❌ 找不到脚本: {script_path}")
            return False

        if not run_script(script_path, desc):
            print(f"\n❌ {desc} 失败")
            return False

    print("\n" + "="*60)
    print("✅ 全部配置完成！")
    print("="*60)

    config_file = skill_root / 'dashboard-config.json'
    if config_file.exists():
        import json
        with open(config_file) as f:
            config = json.load(f)
        print(f"\n📊 仪表盘已创建:")
        print(f"  表: {config.get('table_name')}")
        print(f"  ID: {config.get('table_id')}")
        print(f"\n📍 访问地址:")
        print(f"  {config.get('base_url')}?table={config.get('table_id')}")

    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
