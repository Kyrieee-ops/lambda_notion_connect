import os
import requests
from datetime import datetime, timedelta
from urllib.parse import urlparse
from notion_client import Client

# 環境変数から認証情報取得
QIITA_TOKEN = os.getenv('QIITA_TOKEN')  # Qiitaのアクセストークン
NOTION_TOKEN = os.getenv('NOTION_TOKEN') # Notion Secretキー
NOTION_DB_ID = os.getenv('NOTION_DB_ID') # Notion DBキー

def lambda_handler(event, context):
    try:
        # 1. Qiitaから記事取得
        articles = fetch_qiita_articles()
        
        # 2. Notionクライアント初期化
        notion = Client(auth=NOTION_TOKEN)
        
        # 3. 既存記事のURLを取得
        existing_urls = get_existing_article_urls(notion)
        
        # 4. 新規記事のみフィルタリング
        new_articles = [
            article for article in articles 
            if normalize_url(article["url"]) not in existing_urls
        ]
        
        # 5. Notionに書き込み
        results = []
        for article in new_articles:
            result = create_notion_page(notion, article)
            results.append(result)
        
        return {
            "statusCode": 200,
            "body": {
                "message": f"{len(new_articles)}件の新規記事を登録しました（スキップ: {len(articles) - len(new_articles)}件）",
                "details": results
            }
        }
        
    except Exception as e:
        return {
            "statusCode": 500,
            "body": {"error": str(e)}
        }

def get_existing_article_urls(notion):
    """NotionDBから既存記事のURL一覧を取得"""
    existing_pages = notion.databases.query(
        database_id=NOTION_DB_ID,
        filter={"property": "URL", "url": {"is_not_empty": True}}
    )
    
    return {
        normalize_url(page["properties"]["URL"]["url"])
        for page in existing_pages["results"]
    }

def normalize_url(url):
    """URLを正規化（クエリパラメータや末尾スラッシュを無視）"""
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}{parsed.path}".rstrip("/")

def fetch_qiita_articles():
    """QiitaからKubernetes/EKSタグの記事を取得"""
    url = "https://qiita.com/api/v2/items"
    
    # 検索条件（直近7日間、タグ指定）
    params = {
        "query": "tag:Kubernetes OR tag:EKS created:>={}".format(
            (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        ),
        "per_page": 20  # 最大取得件数
    }
    
    headers = {}
    if QIITA_TOKEN:
        headers["Authorization"] = f"Bearer {QIITA_TOKEN}"
    # print(headers)

    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    
    # print("リクエストボディ:", repr(response.request.body))
    # print("レスポンスボディ:", response.json())

    return response.json()

def create_notion_page(notion, article):
    """Notionにページ作成"""
    # タグ情報を抽出
    tags = [tag["name"] for tag in article.get("tags", [])]
    
    # Notionプロパティ形式に変換
    properties = {
        "Title": {
            "title": [
                {
                    "text": {
                        "content": article["title"]
                    }
                }
            ]
        },
        "URL": {
            "url": article["url"]
        },
        "Date": {
            "date": {
                "start": article["created_at"] # Qiitaの記事作成日を設定
            }
        },
        "Tags": {
            "multi_select": [
                {"name": tag} for tag in tags
            ]
        },
        "作成者": {
            "rich_text": [
                {
                    "text": {
                        "content": article["user"]["id"]
                    }
                }
            ]
        }
    }
    
    # Notionにページ作成
    response = notion.pages.create(
        parent={"database_id": NOTION_DB_ID},
        properties=properties
    )
    print(f"Qiita記事作成日: {article['created_at']}")
    print(f"Notionページ作成日: {response['created_time']}")
    
    
    return {
        "qiita_id": article["id"],
        "notion_id": response["id"],
        "title": article["title"]
    }