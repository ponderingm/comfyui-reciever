# Raspberry Pi 画像受け取りサーバー（Docker）+ Samba 共有（NAS風）

このリポジトリは、Raspberry Pi 上で FastAPI ベースの受信サーバー（Docker コンテナ）を動かし、Google Colab（ComfyUI）から Tailscale 経由で送られてくる画像ファイルを保存します。保存先は Samba コンテナで LAN に共有し、NAS のように扱えます。

## 全体構成
- Google Colab（ComfyUI）で画像生成
- Tailscale で Colab ↔ Raspberry Pi 間の通信（暗号化 VPN）
- Raspberry Pi（受信サーバー）で画像を保存
- Samba で保存フォルダを LAN に共有

## エンドポイント（受信サーバー）
- POST http://<piのTailscale IP>:18080/upload
  - Content-Type: multipart/form-data
  - フィールド:
    - file: 画像ファイル（複数可、同じキー名 `file` を繰り返し）
    - subdir: 任意。保存ルート以下のサブフォルダ名

レスポンス例:
{
  "saved": [
    {"filename": "20250904_121314_original.png", "path": "/data/2025-09-04/20250904_121314_original.png", "size": 123456}
  ]
}

ヘルスチェック:
- GET http://<piのTailscale IP>:18080/health → {"status":"ok"}

## セットアップ手順（Raspberry Pi 側）
1) 前提
   - Docker / Docker Compose がインストール済み
   - Tailscale に接続済み（Pi が tailnet IP を持っている）

2) Samba のユーザー/パスワード設定
   - `.env` を編集して `SAMBA_USER` / `SAMBA_PASS` を設定（初期値はサンプルなので必ず変更推奨）

3) ビルド & 起動
   - 本ディレクトリで以下を実行:
```bash
docker compose up -d --build
```

4) 動作確認
   - ブラウザまたは curl で `http://<piのTailscale IP>:18080/health` を開き、`{"status":"ok"}` が返ればOK

5) 送信テスト（任意のクライアントから）
```bash
curl -X POST \
  -F "file=@/path/to/image.png" \
  http://<piのTailscale IP>:18080/upload
```

6) LAN からの共有アクセス（Samba）
- Windows: `\\<piのLAN IP>\images`
- macOS/Linux: `smb://<piのLAN IP>/images`
  - ユーザー名/パスワードは `.env` の `SAMBA_USER` / `SAMBA_PASS`

### 保存先について
- 受信サーバーは、コンテナ内 `/data`（ホストの `./data` にバインド）に保存します。
- デフォルトで日付ディレクトリ（例: `/data/2025-09-04`）の下に、タイムスタンプ + 元ファイル名で保存します。
- `subdir` を指定すると `/data/<subdir>/<日付>` 配下に保存されます。

## Colab 送信サンプル（Python）
```python
import requests

def send_image(path, host, subdir=None):
    url = f"http://{host}:18080/upload"
    files = [("file", (path.split("/")[-1], open(path, "rb"), "application/octet-stream"))]
    data = {"subdir": subdir} if subdir else {}
    r = requests.post(url, files=files, data=data, timeout=60)
    r.raise_for_status()
    return r.json()

# host には Raspberry Pi の Tailscale IP（例: 100.x.y.z）を指定
```

## 環境変数
- `SAVE_DIR`: 受信サーバーの保存ディレクトリ（コンテナ内パス）。デフォルト `/data`（ホスト側 `./data` にマウント）
- `.env` 内の `SAMBA_USER` / `SAMBA_PASS`: Samba のログイン情報

## よくある問題と対処
- 受信ポートが使用中: `18080` が他プロセスで使用中なら、`docker-compose.yml` の `ports` を編集（例: `19080:8000`）して再起動
- Samba に接続できない/認証失敗: `.env` のユーザー/パスワードを再確認し、コンテナ再作成
- LAN から SMB が見えない: ルーターやファイアウォールで 137/138(UDP), 139/445(TCP) をブロックしていないか確認
- アーキテクチャ: 使用イメージはマルチアーキテクチャ対応（arm64/armv7）。Pi のリソースに余裕があるか確認

## Tips（運用）
- Tailscale 側では、Colab から Pi の tailnet IP:18080 へ HTTP POST できれば動作します。
- LAN 側に公開したくない場合は、`docker-compose.yml` から `samba` サービスを削除（または停止）して受信サーバーのみ運用可能です。

