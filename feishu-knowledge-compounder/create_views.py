#!/usr/bin/env python3
"""
创建仪表盘视图
"""

import os
import sys
import json
import time
from pathlib import Path
from urllib import request, error

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
        print("❌ 缺少凭证")
        return None

    resp = api_call('POST', '/open-apis/auth/v3/tenant_access_token/internal', {
        'app_id': app_id,
        'app_secret': app_secret
    })

    if 'error' in resp:
        print(f"❌ 获取令牌失败")
        return None

    return resp.get('tenant_access_token')

def create_view(base_token, table_id, view_config, token):
    """创建视图"""
    resp = api_call('POST', f'/open-apis/bitable/v1/apps/{base_token}/tables/{table_id}/views',
                   {'view': view_config}, token)

    if 'error' in resp:
        return None

    return resp.get('data', {}).get('view_id')

def main():
    print("="*60)
    print("📊 创建仪表盘视图")
    print("="*60)

    # 加载环境
    env_file = Path('.env')
    if env_file.exists():
        for line in env_file.read_text().strip().split('\n'):
            if line and not line.startswith('#') and '=' in line:
                key, val = line.split('=', 1)
                os.environ[key.strip()] = val.strip().strip('"').strip("'")

    # 读取配置
    config_file = Path('dashboard-config.json')
    if not config_file.exists():
        print(f"❌ 找不到: {config_file}")
        print("   请先运行: python3 create_dashboard.py")
        return False

    with open(config_file) as f:
        config = json.load(f)

    base_token = config['base_token']
    table_id = config['table_id']

    print(f"\n📍 Base: {base_token}")
    print(f"📍 Table: {table_id}")

    # 获取令牌
    print("\n📍 步骤1: 获取令牌...")
    token = get_tenant_token()
    if not token:
        return False
    print(f"✅ 已获取")

    # 定义视图配置
    views_config = [
        {
            'name': '📊 主仪表盘',
            'view_type': 11,  # Grid view
            'filter': None
        },
        {
            'name': '🔧 维度分析',
            'view_type': 11,
            'filter': None
        },
        {
            'name': '🔴 关键待办',
            'view_type': 11,
            'filter': {
                'conditions': [
                    {
                        'field_id': config['fields'].get('优先级'),
                        'operator': 'is',
                        'value': '🔴 关键'
                    }
                ]
            }
        },
        {
            'name': '⏰ 超期未审查',
            'view_type': 11,
            'filter': None
        },
        {
            'name': '📈 时间趋势',
            'view_type': 11,
            'filter': None
        }
    ]

    # 创建视图
    print("\n📍 步骤2: 创建视图...")
    for view in views_config:
        view_payload = {'name': view['name'], 'view_type': view['view_type']}
        if view['filter']:
            view_payload['filter'] = view['filter']

        view_id = create_view(base_token, table_id, view_payload, token)
        if view_id:
            print(f"  ✅ {view['name']}")
            time.sleep(0.5)
        else:
            print(f"  ⚠️  {view['name']} (创建失败)")

    print("\n" + "="*60)
    print("✅ 视图创建完成！")
    print("="*60)
    print(f"\n📍 访问地址:")
    print(f"  {config.get('base_url')}?table={table_id}")

    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
