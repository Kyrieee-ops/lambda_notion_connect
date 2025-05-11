import os
import json
import requests

SLACK_WEBHOOK_URL = os.getenv('SLACK_WEBHOOK_URL')

def lambda_handler(event, context):
    try:
        print(f"受信イベント: {event}")  # lambda_handlerの先頭に追加
        # SNSメッセージを解析
        sns_message = json.loads(event['Records'][0]['Sns']['Message'])
        
        # Slack用メッセージを生成
        slack_msg = build_slack_message(sns_message)
        
        # Slackに送信
        response = requests.post(
            SLACK_WEBHOOK_URL,
            json=slack_msg,
            timeout=3
        )
        response.raise_for_status()
        
        return {"statusCode": 200}
    
    except Exception as e:
        print(f"Slack通知失敗: {str(e)}")
        # 必要に応じてCloudWatch LogsやDead Letter Queueへ
        raise e

def build_slack_message(sns_msg):
    """SNSメッセージからSlack用ブロックを生成"""
    if sns_msg["status"] == "SUCCESS":
        return {
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"✅ *同期成功*: {sns_msg['message']}"
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*処理日時*\n{sns_msg['timestamp']}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*詳細*\n{sns_msg['details']}"
                        }
                    ]
                }
            ]
        }
    else:
        return {
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"❌ *同期失敗*: {sns_msg['message']}"
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"```{sns_msg['details']['error']}```"
                    }
                }
            ]
        }