#!/usr/bin/env python3
"""
自动创建知识沉淀管理仪表盘
在飞书多维表格中创建完整的仪表盘系统
"""

import os
import sys
import json
import time
from pathlib import Path
from urllib import request, error, parse

# 加载环境
env_file = Path('.env')
if env_file.exists():
    for line in env_file.read_text().strip().split('\n'):
        if line and not line.startswith('#'):
            if '=' in line:
                key, val = line.split('=', 1)
                os.environ[key.strip()] = val.strip().strip('"').strip("'")

def api_call(method, endpoint, payload=None, token=None):
    """调用飞书 API"""
    base_url = "https://open.feishu.cn"
    url = f"{base_url}{endpoint}"

    headers = {'Content-Type': 'application/json'}
    if token:
        headers['Authorization'] = f'Bearer {token}'

    data = json.dumps(payload).encode() if payload else None
    req = request.Request(url, data=data, headers=headers, method=method)

    try:
        with request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except error.HTTPError as e:
        body = e.read().decode()
        return {'error': f'HTTP {e.code}', 'body': body}
    except Exception as e:
        return {'error': str(e)}

def get_tenant_token():
    """获取租户访问令牌"""
    app_id = os.getenv('FEISHU_APP_ID')
    app_secret = os.getenv('FEISHU_APP_SECRET')

    if not app_id or not app_secret:
        print("❌ 缺少 FEISHU_APP_ID 或 FEISHU_APP_SECRET")
        return None

    resp = api_call('POST', '/open-apis/auth/v3/tenant_access_token/internal', {
        'app_id': app_id,
        'app_secret': app_secret
    })

    if 'error' in resp:
        print(f"❌ 获取令牌失败: {resp}")
        return None

    return resp.get('tenant_access_token')

def create_table(base_token, table_name, token):
    """创建新表"""
    resp = api_call('POST', f'/open-apis/bitable/v1/apps/{base_token}/tables', {
        'table': {'name': table_name}
    }, token)

    if 'error' in resp:
        print(f"❌ 创建表失败: {resp}")
        return None

    return resp['data']['table_id']

def get_fields(base_token, table_id, token):
    """获取表的现有字段"""
    resp = api_call('GET', f'/open-apis/bitable/v1/apps/{base_token}/tables/{table_id}/fields', token=token)

    if 'error' in resp:
        print(f"❌ 获取字段失败: {resp}")
        return {}

    return {f['field_name']: f['field_id'] for f in resp.get('data', {}).get('items', [])}

def create_field(base_token, table_id, field_config, token):
    """创建单个字段"""
    resp = api_call('POST', f'/open-apis/bitable/v1/apps/{base_token}/tables/{table_id}/fields',
                   {'field': field_config}, token)

    if 'error' in resp:
        return None

    return resp['data']['field_id']

def main():
    print("="*60)
    print("🚀 飞书知识沉淀管理仪表盘 - 自动配置")
    print("="*60)

    # 读取配置
    config_file = Path('feishu-config.json')
    if not config_file.exists():
        print(f"❌ 找不到配置文件: {config_file}")
        return False

    with open(config_file) as f:
        config = json.load(f)

    base_token = config['app_token']
    print(f"\n📍 Base: {base_token}")

    # 获取令牌
    print("\n📍 步骤1: 获取租户访问令牌...")
    token = get_tenant_token()
    if not token:
        return False
    print(f"✅ 已获取")

    # 创建表
    print("\n📍 步骤2: 创建表...")
    table_name = "知识沉淀仪表盘"
    table_id = create_table(base_token, table_name, token)
    if not table_id:
        return False
    print(f"✅ 表已创建: {table_id}")

    time.sleep(2)

    # 获取现有字段
    print("\n📍 步骤3: 检查现有字段...")
    existing_fields = get_fields(base_token, table_id, token)
    print(f"✅ 找到 {len(existing_fields)} 个默认字段")

    # 定义要创建的字段
    fields_config = [
        {
            'field_name': '知识ID',
            'type': 'text',
            'ui_type': 'text'
        },
        {
            'field_name': '标题',
            'type': 'text',
            'ui_type': 'text'
        },
        {
            'field_name': '内容摘要',
            'type': 'rich_text',
            'ui_type': 'rich_text'
        },
        {
            'field_name': '来源类型',
            'type': 'single_select',
            'ui_type': 'single_select',
            'property': {
                'options': [
                    {'text': '手动沉淀', 'color': 1},
                    {'text': '自动挖掘', 'color': 3}
                ]
            }
        },
        {
            'field_name': '沉淀时间',
            'type': 'date',
            'ui_type': 'date',
            'property': {'date_formatter': 'yyyy-MM-dd'}
        },
        {
            'field_name': '价值等级',
            'type': 'single_select',
            'ui_type': 'single_select',
            'property': {
                'options': [
                    {'text': '⭐⭐⭐ 高', 'color': 0},
                    {'text': '⭐⭐ 中', 'color': 5},
                    {'text': '⭐ 低', 'color': 8}
                ]
            }
        },
        {
            'field_name': '价值维度',
            'type': 'multi_select',
            'ui_type': 'multi_select',
            'property': {
                'options': [
                    {'text': '🔧 技术', 'color': 2},
                    {'text': '💼 业务', 'color': 3},
                    {'text': '🚀 个人成长', 'color': 4},
                    {'text': '👔 管理', 'color': 5},
                    {'text': '📌 其他', 'color': 8}
                ]
            }
        },
        {
            'field_name': '优先级',
            'type': 'single_select',
            'ui_type': 'single_select',
            'property': {
                'options': [
                    {'text': '🔴 关键', 'color': 0},
                    {'text': '🟡 重要', 'color': 5},
                    {'text': '⚪ 普通', 'color': 8}
                ]
            }
        },
        {
            'field_name': '状态',
            'type': 'single_select',
            'ui_type': 'single_select',
            'property': {
                'options': [
                    {'text': '📝 新增', 'color': 8},
                    {'text': '✅ 已审查', 'color': 2},
                    {'text': '🚀 已行动', 'color': 3}
                ]
            }
        },
        {
            'field_name': '关联链接',
            'type': 'url',
            'ui_type': 'url'
        },
        {
            'field_name': '最后更新时间',
            'type': 'modified_time',
            'ui_type': 'modified_time',
            'property': {'date_formatter': 'yyyy-MM-dd HH:mm'}
        }
    ]

    # 创建字段
    print("\n📍 步骤4: 创建字段...")
    created_fields = {}

    for field in fields_config:
        field_name = field['field_name']

        if field_name in existing_fields:
            print(f"  ⏭️  {field_name} (已存在)")
            created_fields[field_name] = existing_fields[field_name]
        else:
            field_id = create_field(base_token, table_id, field, token)
            if field_id:
                print(f"  ✅ {field_name}")
                created_fields[field_name] = field_id
                time.sleep(0.3)
            else:
                print(f"  ⚠️  {field_name} (创建失败)")

    print(f"\n✅ 共创建/识别 {len(created_fields)} 个字段")

    # 保存配置
    print("\n📍 步骤5: 保存配置...")
    dashboard_config = {
        'base_token': base_token,
        'table_id': table_id,
        'table_name': table_name,
        'fields': created_fields,
        'base_url': config.get('base_url', 'https://trip.larkenterprise.com'),
        'created_at': time.strftime('%Y-%m-%d %H:%M:%S')
    }

    with open('dashboard-config.json', 'w') as f:
        json.dump(dashboard_config, f, indent=2, ensure_ascii=False)

    print("✅ 配置已保存")

    print("\n" + "="*60)
    print("✅ 自动配置完成！")
    print("="*60)
    print(f"\n📊 仪表盘信息:")
    print(f"  表名: {table_name}")
    print(f"  表ID: {table_id}")
    print(f"  字段数: {len(created_fields)}")
    print(f"\n📍 访问地址:")
    print(f"  {config.get('base_url', 'https://trip.larkenterprise.com')}?table={table_id}")
    print(f"\n💾 配置文件: dashboard-config.json")

    print("\n📝 下一步: 创建视图")
    print("  运行: python3 create_views.py")

    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
