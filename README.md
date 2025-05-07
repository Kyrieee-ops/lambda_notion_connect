# LambdaからQiita APIを使って対象タグの記事をNotionDBに登録

## 環境
- AWS Lambda
- Runtime: Python3.12

## 前提
- Pythonがインストールされていること
- Lambdaの一般設定でタイムアウト1分, メモリ: 1024MBに設定
- Notion Secretキーが発行済みで、対象のNotionページに連携していること
- Qiitaから取得する情報とNotionDBのカラムの内容が一致していること(今回であれば、タイトル、URL、Qiitaの記事作成日、タグ、Qiita記事の作成者のカラムが存在すること)

## 事前準備
1. notion_clientライブラリのインストール
```bash
mkdir python
cd python
# 作成したディレクトリにnotion-clientをインストール
pip install notion-client -t .
cd ../
# pythonディレクトリを再帰的にzipし、Lambdaレイヤーを作成
zip -r notion_layer.zip python
```

2. AWS Lambdaコンソールから新しいレイヤーを作成し、zipをアップロード
3. Lambda関数を作成し、レイヤーを追加

## 環境変数の定義
- Lambdaコンソールの設定から環境変数をクリック
- 編集で以下のキーと値を作成
    - キー: NOTION_DB_ID, 値: 実際のNotionのデータベースID
    - キー: NOTION_TOKEN, 値: NotionIntegrationで作成したSecretsキ- キー: QIITA_TOKEN, 値: 実際のQiitaアクセストークン

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


## 参考
Qiitaアクセストークン発行方法
- https://qiita.com/miyuki_samitani/items/bfe89abb039a07e652e6