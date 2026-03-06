# NeonPDF Shot (Windows)

ローカル環境で動作する、ドラッグ&ドロップ対応の PDF -> JPG 変換アプリです。

企業PC向けに、Python依存をなくした `.NET 8 (WPF)` 版を同梱しています。

## Features

- 1ファイル/複数ファイルの PDF をまとめて変換
- ドラッグ&ドロップで簡単投入
- 出力先フォルダを選択可能
- DPI と JPG 品質を調整可能
- オフライン変換 (PDF を外部送信しない)

## Quick Start (Windows / .NET 8版)

プロジェクト直下で実行:

```bat
powershell -ExecutionPolicy Bypass -File scripts\build_windows_dotnet.ps1
```

これで以下を一気に実行します。

- .NET アプリを self-contained で publish
- Pythonランタイム不要の配布物を生成

生成物:

- 通常: `dist-dotnet\NeonPDFShot\NeonPDFShot.exe`
- 単一ファイル: `powershell -ExecutionPolicy Bypass -File scripts\build_windows_dotnet.ps1 -SingleFile`

## MacからWindows成果物を作る (GitHub Actions)

Mac環境でも、GitHub ActionsでWindows向け `exe` とインストーラーを自動生成できます。

1. このプロジェクトをGitHubにpush
2. GitHubの `Actions` タブで `Build Windows Artifacts` を実行
3. 実行完了後、Artifactsから以下をダウンロード

- `NeonPDFShot-app` (実行ファイル一式)
- `NeonPDFShot-installer` (セットアップexe)

workflow定義:

- `.github/workflows/windows-build.yml`

## Manual Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

※ こちらは旧Python版 (`app.py`) の実行手順です。

## Run

```bash
python app.py
```

## Build EXE (Windows)

```powershell
powershell -ExecutionPolicy Bypass -File scripts/build_windows_dotnet.ps1
```

生成物は `dist-dotnet/NeonPDFShot/` 配下に作られます。

## Build Installer (.exe)

1. Inno Setup をインストール
2. 先に `scripts\build_windows_dotnet.ps1` でアプリ本体をビルド
3. 次を実行

```powershell
powershell -ExecutionPolicy Bypass -File scripts/make_installer.ps1
```

生成物:

- `dist-installer\NeonPDFShot-Setup-1.0.0.exe`

Inno Setup 設定ファイル:

- `installer/NeonPDFShot.iss`

## Usage

1. PDF を画面にドロップ (または `Select PDF files`)
2. 出力フォルダを指定
3. DPI / JPG Quality を調整
4. `Convert to JPG` を実行

## Notes

- スキャンPDFなどページ数が多い場合は変換に時間がかかります。
- ファイル名は `<pdf名>_page_001.jpg` 形式で保存されます。
- 企業配布時は、署名済みインストーラーを推奨します (AppLocker/WDAC対策)。
