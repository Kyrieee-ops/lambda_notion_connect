# LambdaからQiita APIを使って対象タグの記事をNotionDBに登録

## 環境
- AWS Lambda
- Runtime: Python3.12

## 前提
作り方の詳細は別途Qiita等にまとめる予定です。

以下は簡易的な手順や仕様説明となります。

- Pythonがインストールされていること
- Lambdaの一般設定でタイムアウト1分, メモリ: 1024MBに設定
- Notion Secretキーが発行済みで、対象のNotionページに連携していること
- Qiitaから取得する情報とNotionDBのカラムの内容が一致していること(今回であれば、タイトル、URL、Qiitaの記事作成日、タグ、Qiita記事の作成者のカラムが存在すること)

## 事前準備
1. notion_clientライブラリのインストール
2. requestsライブラリをARNで指定する -> 参照の記事を参考にする

```bash
mkdir python
cd python
# 作成したディレクトリにnotion-clientをインストール
pip install notion-client -t .
cd ../
# pythonディレクトリを再帰的にzipし、Lambdaレイヤーを作成
zip -r notion_layer.zip python
```

2. AWS Lambdaコンソールから新しいレイヤーを作成し、notion_layer.zipをアップロード
3. Lambda関数を作成し、レイヤーを追加(notion_layer, Klayers-p312-requests)
4. eventbridge-scheduler-lambda.yamlをCloudFormationでデプロイ
5. SNSトピックを作成し、サブスクリプションを以下のように作成
    - トピックARN: 作成したSNSトピックのARNを指定
    - プロトコル: Lambda
    - エンドポイント: Slack通知用LambdaのARNを指定
6. メインLambdaの実行ロールにSNS実行権限を付与

policy全体

```json
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": "logs:CreateLogGroup",
            "Resource": "arn:aws:logs:${AWS::Region}:${AWS::AccountId}:*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "logs:CreateLogStream",
                "logs:PutLogEvents"
            ],
            "Resource": [
                "arn:aws:logs:${AWS::Region}:${AWS::AccountId}:log-group:/aws/lambda/notion-connect:*"
            ]
        },
        {
            "Effect": "Allow",
            "Action": "sns:Publish",
            "Resource": "arn:aws:sns:${AWS::Region}:${AWS::AccountId}:slack-notifications-lambda-notion"
        }
    ]
}

```

## 環境変数の定義
Lambdaは2つあり、メインLambdaのLambdaとSlack通知用のLambdaの二つがあります

### メインLambda
- Lambdaコンソールの設定から環境変数をクリック
- 編集で以下のキーと値を作成
    - キー: NOTION_DB_ID, 値: 実際のNotionのデータベースID
    - キー: NOTION_TOKEN, 値: NotionIntegrationで作成したSecrets
    - キー: QIITA_TOKEN, 値: 実際のQiitaアクセストークン
    - キー: SNS_TOPIC_ARN, 値: arn:aws:sns:${AWS::Region}:${AWS::AccountId}:slack-notifications-lambda-notion

### Slack通知用Lambda
- Lambdaコンソールの設定から環境変数をクリック
- 編集で以下のキーと値を作成
    - キー: SLACK_WEBHOOK_URL, 値: Slackから発行したIncomming　Webhook URL

## 仕様
- Qiita APIを使って`Kubernetes`, `EKS`のタグの付いた本日から換算して直近7日間のQiita記事をNotionDBに登録します。
- 過去にNotionDBに登録のある記事は重複して記事を取得しません。
- タグを別のタグにして取得したい場合は、以下の`query: "tag:Kubernetes OR tag:EKS created:>={}`内容を適宜修正してください。
```python
    # 検索条件（直近7日間、タグ指定）
    params = {
        "query": "tag:Kubernetes OR tag:EKS created:>={}".format(
            (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        ),
        "per_page": 20  # 最大取得件数
    }
```
- 記事の取得上限数を20に設定しています。上限を引き上げたい、もしくは引き下げたい場合はこの数字を修正してください。
- メインLambdaはEventBridge Schedulerによって毎週月曜12時に実行され、SNSトピックがPublish、Slack通知用Lambdaに連携し、Slackに通知が流れる仕組みです。

## 参考
Qiitaアクセストークン発行方法
- https://qiita.com/miyuki_samitani/items/bfe89abb039a07e652e6
Lambdaの外部レイヤーを利用するときのKlayersについて
- https://zenn.dev/ndjndj/articles/2533d854d86902