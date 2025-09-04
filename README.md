# Google Drive フェッチャーで画像を自動取得・即削除（Raspberry Pi / Docker）

このリポジトリは、Google Colab（ComfyUI）で生成した画像をGoogle Driveに一時保存し、Raspberry Pi 上のDockerコンテナが自動で取得してDriveから削除する仕組みを提供します。NSFW画像などをDriveに残したくないケースを想定しています。

Tailscale は不要です。Colab → Drive → Pi（フェッチ） の非同期フローで安全に運用できます。

## 全体構成
- Google Colab（ComfyUI）で画像生成 → Driveの指定フォルダへ保存
- Raspberry Pi 上の `drive_fetcher` コンテナが定期ポーリングで画像を検出
- 見つけた画像をPiへダウンロード後、Driveから即削除
- （任意）`samba` コンテナでダウンロード済みフォルダをLAN共有
- （任意）従来の受信サーバー（`receiver`）も残してありますが、標準フローでは不要です

## セットアップ（Raspberry Pi 側）
1) 前提
   - Docker / Docker Compose がインストール済み
   - 本リポジトリをPi上に配置

2) Google Drive API 認証（サービスアカウント）
   - Google Cloud でプロジェクト作成 → Drive API を有効化
   - サービスアカウントを作成し、JSON鍵をダウンロード
   - Pi上で `drive_creds/` ディレクトリを作成し、`service_account.json` を配置

3) フェッチャー起動（初回ビルド込み）
```bash
docker compose up -d --build drive_fetcher
```

4) 保存先
   - ダウンロードされたファイルはリポジトリ直下の `./downloads` に保存されます
   - 保存後、Drive上の元ファイルは即削除されます

5) 監視対象やポーリング間隔の調整（環境変数）
   - `DRIVE_QUERY`: 検索クエリ（初期値: `mimeType contains 'image/'`）
   - `DRIVE_FOLDER_ID`: 特定フォルダのみ監視したい場合に設定
   - `POLL_INTERVAL`: ポーリング間隔（秒）

## Colab 側（例）
Colabで生成した画像をDriveの特定フォルダに保存してください（例: `MyDrive/ComfyUI/exports`）。`DRIVE_FOLDER_ID` を設定すると、そのフォルダのみをPiが監視します。保存終了後、Piが自動で取得・Driveから削除します。

## 共有（任意：Samba）
Pi上のダウンロードフォルダをLANで共有したい場合は `samba` サービスを使えます。
- `.env` の `SAMBA_USER` / `SAMBA_PASS` を設定
- 起動:
```bash
docker compose up -d samba
```
- アクセス:
  - Windows: `\\<piのLAN IP>\images`
  - macOS/Linux: `smb://<piのLAN IP>/images`

## 受信サーバー（任意）
従来のHTTP受信サーバー（FastAPI）は `receiver` ディレクトリに残しています。Tailscaleなし運用では不要ですが、外部から直接POSTしたい場合に利用できます。
- 起動:
```bash
docker compose up -d receiver
```
- ヘルスチェック: `http://<piのLAN IP>:18080/health`
- アップロード: `POST /upload`（multipart/form-data の `file`、任意 `subdir`）
- 保存仕様: `/data/<任意subdir>/<YYYY-MM-DD>/<YYYYMMDD_HHMMSS_ffffff>_<元ファイル名>`

## 環境変数（抜粋）
- drive_fetcher
  - `GOOGLE_APPLICATION_CREDENTIALS`（固定: `/creds/service_account.json`）
  - `DOWNLOAD_DIR`（固定: `/downloads` → ホストの `./downloads` にマウント）
  - `DRIVE_QUERY`（例: `mimeType contains 'image/'`）
  - `DRIVE_FOLDER_ID`（オプション）
  - `POLL_INTERVAL`（秒）
- samba（任意）
  - `.env` の `SAMBA_USER` / `SAMBA_PASS`
- receiver（任意）
  - `SAVE_DIR`（デフォルト `/data` → ホストの `./data` にマウント）

## よくある質問（FAQ）
- Q: なぜTailscaleが不要になったの？
  - A: 画像はDriveを介して非同期に取得するため、ColabからPiへ直接到達する必要がありません。
- Q: Driveに画像が残りませんか？
  - A: フェッチャーがダウンロード後にDriveから削除します。ポーリング間隔内（既定60秒）は一時的に存在します。
- Q: 特定フォルダだけを対象にできますか？
  - A: `DRIVE_FOLDER_ID` を設定してください。そのフォルダ配下のみが対象になります。
- Q: 受信サーバーと併用できますか？
  - A: はい。用途に応じて `receiver` を併用可能です（デフォルトでは不要）。

## ライセンス / 注意
- 本ツールは自己責任でご利用ください。各種利用規約（Google/Colab/Drive等）に従って運用してください。

