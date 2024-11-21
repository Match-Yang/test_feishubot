import json
import os
import requests
import yaml

def load_user_mapping():
    """加载用户映射配置"""
    with open('.github/configs/user_mapping.yml', 'r') as f:
        return yaml.safe_load(f)

def get_changed_files():
    """获取PR中变更的文件列表"""
    pr_number = os.environ['GITHUB_EVENT_PATH']
    with open(pr_number, 'r') as f:
        event_data = json.load(f)
    
    # 获取变更文件列表
    changed_files = []
    if 'pull_request' in event_data:
        api_url = event_data['pull_request']['url'] + '/files'
        response = requests.get(api_url)
        if response.status_code == 200:
            files_data = response.json()
            changed_files = [file['filename'] for file in files_data]
    
    return changed_files

def determine_webhooks(changed_files):
    """根据变更文件确定需要通知的webhook"""
    webhooks = set()
    
    for file in changed_files:
        if file.startswith('uikit/'):
            webhooks.add(('WEBHOOK_UIKIT', 'API_KEY_UIKIT'))
        elif file.startswith('core_products/zim/'):
            webhooks.add(('WEBHOOK_ZIM', 'API_KEY_ZIM'))
    
    return webhooks

def get_pr_status():
    """获取PR状态"""
    event = os.environ['PR_EVENT']
    action = os.environ['PR_ACTION']
    
    if action == 'opened':
        return "新建PR"
    elif action == 'synchronize':
        return "更新PR"
    elif action == 'closed':
        with open(os.environ['GITHUB_EVENT_PATH'], 'r') as f:
            event_data = json.load(f)
        if event_data['pull_request']['merged']:
            return "合并PR"
        return "关闭PR"
    return "未知状态"

def send_to_feishu(webhook_url, api_key, message):
    """发送消息到飞书"""
    headers = {
        'Content-Type': 'application/json'
    }
    
    payload = {
        "msg_type": "interactive",
        "card": {
            "config": {
                "wide_screen_mode": True
            },
            "header": {
                "title": {
                    "tag": "plain_text",
                    "content": message['title']
                },
                "template": "blue"
            },
            "elements": [
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": message['content']
                    }
                },
                {
                    "tag": "action",
                    "actions": [
                        {
                            "tag": "button",
                            "text": {
                                "tag": "plain_text",
                                "content": "查看 PR"
                            },
                            "url": message['pr_url'],
                            "type": "default"
                        }
                    ]
                }
            ]
        }
    }
    
    try:
        response = requests.post(
            webhook_url,
            headers=headers,
            json=payload
        )
        print(f"发送状态: {response.status_code}")
        print(response.text)
    except Exception as e:
        print(f"发送失败: {str(e)}")

def main():
    # 读取GitHub事件数据
    with open(os.environ['GITHUB_EVENT_PATH'], 'r') as f:
        event_data = json.load(f)
    
    pr_data = event_data['pull_request']
    user_mapping = load_user_mapping()
    
    # 获取PR创建者的飞书ID
    github_user = pr_data['user']['login']
    feishu_user = user_mapping.get(github_user, github_user)
    
    # 构建消息
    message = {
        'title': pr_data['title'],
        'content': f"**状态**: {get_pr_status()}\n**创建者**: <at id={feishu_user}></at>\n**描述**: {pr_data['body'] or '无'}",
        'pr_url': pr_data['html_url']
    }
    
    # 获取变更文件并确定需要通知的webhook
    changed_files = get_changed_files()
    webhooks = determine_webhooks(changed_files)
    
    # 发送通知
    for webhook_env, api_key_env in webhooks:
        webhook_url = os.environ.get(webhook_env)
        api_key = os.environ.get(api_key_env)
        if webhook_url and api_key:
            send_to_feishu(webhook_url, api_key, message)

if __name__ == "__main__":
    main() 