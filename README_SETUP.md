# 東京ぶらり旅プロジェクト アプリ

「東京電車プロジェクト」で育ててきた、自分で目的を決め、情報を探し、人やモノからヒントを得て判断し、前に進む力を土台にした発展版です。

このアプリでは、旅の目的を「目的駅への到達」ではなく、街の中で本人の「気になる」を増やし、あとから自分の経験を読み返せる形で残すことに置いています。

## 4つの画面

### 1. 📷 ぶらり旅
- 行き先メモは任意
- 旅を始めるとカメラを表示
- 気になるものだけ撮影
- その場で理由を答えさせない
- 既にスマホで撮った写真も追加可能

### 2. 📖 今日の日記
- 写真を1枚ずつ表示
- AIが写真を見て、5〜6歳向けの短い質問を1つずつ音声で出す
- 子どもはマイクで回答
- 1枚につき原則2〜3回答以内で終了
- AIは感情や「便利・不便」を決めつけない
- 最後に本人の発言だけから短い日記を作成
- 子どもが音声で修正してから保存可能

### 3. 📚 これまで
- 写真と日記を時系列で読み返す
- AIが日記の根拠にした本人の言葉も確認可能

### 4. 🔍 今月の発見
- 1か月分の日記・本人の発言を横断して振り返る
- 「○○な子」「観察力○点」のような評価・分類はしない
- 違う日に繰り返し出た「気になる」や、本人が実際に言った「こうだったらいい」を返す
- 最後に子ども自身が考える短い問いを1つ返す

## 構成

Android / iPhone / iPad / PC ブラウザ  
→ Streamlit Community Cloud  
→ OpenAI API  
→ Supabase Database + private Storage

Supabase StorageのPython APIは、private bucketへのupload/downloadをサーバー側から行います。

## ファイル

- `app.py`：本体
- `requirements.txt`：依存パッケージ
- `supabase_schema.sql`：テーブル + private写真bucket
- `secrets.toml.example`：Streamlit Secrets例
- `.streamlit/config.toml`：Streamlit設定

## 導入

### 1. Supabase

Supabase SQL Editorで `supabase_schema.sql` を1回実行します。

作成されるもの：
- `burari_trips`
- `burari_photos`
- `burari_diaries`
- `burari_monthly_reviews`
- private Storage bucket `burari-photos`

写真は公開URLにせず、private bucketに保存します。

### 2. GitHub

このフォルダの中身をRepositoryへアップロードします。

Public Repositoryでもソース内に秘密情報は入っていませんが、実際のAPI Key / Supabase Secretは絶対にGitHubへ置かず、Streamlit Secretsにのみ登録してください。

### 3. Streamlit Community Cloud

- Branch: `main`
- Main file path: `app.py`
- Python: 3.12

Advanced settings > Secrets に `secrets.toml.example` を参考に設定します。

最低限必要：
- `OPENAI_API_KEY`
- `SUPABASE_URL`
- `SUPABASE_SECRET_KEY`

写真と日記を扱うため、`FAMILY_PIN` の設定を推奨します。

## 設計上の重要点

### AIは「評価者」ではなく「鏡」

月次振り返りで、AIは子どもの能力や性格を診断しません。保存された本人の言葉の共通点を返し、本人が自分で意味を考えられるようにします。

### AIは日記を創作しない

日記は子どもが写真を見て話した内容だけを材料にします。本人が言っていない感情・出来事・理由を補完しないようプロンプトで制約しています。

### 旅の最中は入力作業を増やさない

その場で「どう思った？」「課題は？」と質問せず、基本は写真を撮るだけです。振り返りは帰宅後に分離します。

### 写真の扱い

- private Supabase Storageへ保存
- AIが写真を読むのは、写真を使って日記の会話を始めたとき
- OpenAI Responses APIは `store=False` で呼び出し
- 人の顔、住所、学校名など個人が分かる情報は必要以上に撮らない運用を推奨

## 最初に確認したい動作

1. 家族PINでログインできる
2. ぶらり旅を開始できる
3. スマホ/タブレットでカメラ権限を許可できる
4. 写真を保存できる
5. 「今日はここまで」で日記画面へ移る
6. 写真を見ながらAIの質問音声が再生される
7. 子どもの音声が文字起こしされる
8. 日記が生成・修正・保存できる
9. 「これまで」で写真と日記が見える
10. 日記が複数たまったら「今月の発見」が生成できる
