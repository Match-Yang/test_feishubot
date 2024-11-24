import os
import json
import sys
from urllib import request, error
from typing import Dict, List, Optional

class NotificationSender:
    def __init__(self):
        self.user_mapping = {}  # 用户映射字典
        
    def get_feishu_id(self, github_user: str) -> Optional[str]:
        """获取用户的飞书 ID"""
        return self.user_mapping.get(github_user)
    
    def load_user_mapping(self, mapping_file: str) -> None:
        """加载用户映射配置"""
        try:
            if os.path.exists(mapping_file):
                with open(mapping_file, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            github_user, feishu_id = line.split('=', 1)
                            self.user_mapping[github_user.strip()] = feishu_id.strip()
        except Exception as e:
            print(f"加载用户映射出错: {e}")
    
    def check_notification_targets(self, config_file: str, changed_files_path: str) -> Dict[str, bool]:
        """检查需要通知的目标"""
        notify_targets = {}
        
        try:
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            path, webhook = line.split('=', 1)
                            path = path.strip()
                            webhook = webhook.strip()
                            
                            if os.path.exists(changed_files_path):
                                with open(changed_files_path, 'r') as cf:
                                    changed_files = cf.read().splitlines()
                                    
                                for changed_file in changed_files:
                                    if changed_file.startswith(path):
                                        notify_targets[webhook] = True
                                        print(f"发现 {path} 相关变更，将通知 {webhook}")
        except Exception as e:
            print(f"检查通知目标出错: {e}")
            
        return notify_targets

    def set_status_and_content(self) -> tuple:
        """设置 PR 状态和额外内容"""
        status = ""
        extra_content = ""
        event_type = os.environ.get('EVENT_TYPE', '')
        
        if event_type == 'pull_request_target':
            pr_action = os.environ.get('PR_ACTION', '')
            if pr_action == 'opened':
                status = "🆕 新建 PR"
                extra_content = f"\n**描述**: {os.environ.get('PR_BODY', '')}"
            elif pr_action == 'closed':
                status = "✅ PR 已合并" if os.environ.get('PR_MERGED') == 'true' else "❌ PR 已关闭"
            else:
                status = "🔄 PR 更新"
                
        elif event_type == 'pull_request_review':
            reviewer = os.environ.get('REVIEWER', '')
            reviewer_id = self.get_feishu_id(reviewer)
            reviewer_text = f"**评审者**: <at id={reviewer_id}></at>" if reviewer_id else f"**评审者**: {reviewer}"
            
            review_state = os.environ.get('REVIEW_STATE', '')
            if review_state == 'approved':
                status = "👍 审核通过"
            elif review_state == 'changes_requested':
                status = "📝 需要修改"
            elif review_state == 'commented':
                status = "💬 收到评审意见"
                
            extra_content = f"\n{reviewer_text}\n**评审意见**: {os.environ.get('REVIEW_BODY', '')}"
            
        elif event_type == 'issue_comment':
            comment_user = os.environ.get('COMMENT_USER', '')
            commenter_id = self.get_feishu_id(comment_user)
            commenter_text = f"**评论者**: <at id={commenter_id}></at>" if commenter_id else f"**评论者**: {comment_user}"
            status = "💬 PR评论"
            extra_content = f"\n{commenter_text}\n**评论内容**: {os.environ.get('COMMENT_BODY', '')}"
            
        # 处理创建者信息
        creator = os.environ.get('PR_CREATOR', '')
        creator_id = self.get_feishu_id(creator)
        creator_text = f"**创建者**: <at id={creator_id}></at>" if creator_id else f"**创建者**: {creator}"
        
        return status, creator_text, extra_content

    def build_message_card(self, status: str, creator_text: str, extra_content: str) -> dict:
        """构建消息卡片"""
        return {
            "msg_type": "interactive",
            "card": {
                "header": {
                    "title": {
                        "tag": "plain_text",
                        "content": os.environ.get('PR_TITLE', '')
                    },
                    "template": "blue"
                },
                "elements": [
                    {
                        "tag": "div",
                        "text": {
                            "tag": "lark_md",
                            "content": f"**状态**: {status}\n{creator_text}{extra_content}"
                        }
                    },
                    {
                        "tag": "hr"
                    },
                    {
                        "tag": "action",
                        "actions": [
                            {
                                "tag": "button",
                                "text": {
                                    "tag": "lark_md",
                                    "content": "查看 PR 👉"
                                },
                                "url": os.environ.get('PR_URL', ''),
                                "type": "default"
                            }
                        ]
                    }
                ]
            }
        }

    def send_notification(self, webhook_url: str) -> None:
        """发送通知"""
        status, creator_text, extra_content = self.set_status_and_content()
        message_card = self.build_message_card(status, creator_text, extra_content)
        
        try:
            data = json.dumps(message_card).encode('utf-8')
            req = request.Request(
                webhook_url,
                data=data,
                headers={
                    "Content-Type": "application/json",
                    "User-Agent": "Python/NotificationBot"
                },
                method='POST'
            )
            
            with request.urlopen(req) as response:
                response_text = response.read().decode('utf-8')
                print(f"飞书响应: {response_text}")
                
        except error.URLError as e:
            print(f"发送通知失败: {e}")
        except Exception as e:
            print(f"发送通知时发生错误: {e}")

    def run(self):
        """运行通知流程"""
        self.load_user_mapping('.github/configs/user_mapping.txt')
        notify_targets = self.check_notification_targets(
            '.github/configs/notification_targets.txt',
            'changed_files.txt'
        )
        
        # 发送通知
        for webhook_env_name in notify_targets:
            print(f"webhook_env_name: {webhook_env_name}")
            webhook_url = os.environ.get(webhook_env_name)
            if webhook_url:
                self.send_notification(webhook_url)
            else:
                print(f"警告：找不到环境变量 {webhook_env_name}")

if __name__ == "__main__":
    sender = NotificationSender()
    sender.run() 