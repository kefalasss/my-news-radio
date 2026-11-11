# My News Radio

ゲーム開発・3DCG・AIのニュースを、キャラクターが日本語で読み上げる個人ラジオです。

**放送ページ:** https://kefalasss.github.io/my-news-radio/

## 自動化

毎朝 **日本時間 06:20** にGitHub Actionsが実行されます。

1. RSS/Atomからゲーム・CG・開発関連記事を収集
2. GEMINI_API_KEY があればGemini APIの無料枠モデルで日本語台本を作成
   - キーがない／API障害時は **RSS見出し読み上げモード** に自動切替（AI要約なし）
3. Open JTalkで音声を生成し、文章ごとの字幕タイミングを記録
4. 台本を main に保存。音声は main に入れず、放送用 gh-pages に直近30日分のみ保存
5. GitHub PagesへActionsから公開

**重要:** [Pages設定](https://github.com/kefalasss/my-news-radio/settings/pages) の Source を
**GitHub Actions** に変更してください。以前の Deploy from a branch のままでは
Actionsからのサイト公開が完了しません。

### 初回実行

1. [Actions → Daily News Radio](https://github.com/kefalasss/my-news-radio/actions/workflows/daily-radio.yml)
2. **Run workflow** → main → **Run workflow**
3. 実行ログにエラーがないか確認
4. [放送ページ](https://kefalasss.github.io/my-news-radio/) を開いて再生

音声はOpen JTalkのデフォルト声（機械的な男性音声）です。あとからVOICEVOX等に差し替えられます。

### AIで要約もしたいとき（任意）

- [Google AI Studio](https://aistudio.google.com/app/apikey) で無料枠のAPIキーを取得
- [Actions Secrets](https://github.com/kefalasss/my-news-radio/settings/secrets/actions) に、名前 GEMINI_API_KEY で登録
- デフォルトは gemini-3.5-flash-lite。モデルの利用可能性や無料枠は変動します
- **キーをリポジトリ、Issue、チャットに貼り付けない**
- 課金を有効にしたプロジェクトのAPIキーでは料金が発生し得るため、無料枠設定を確認

### トラブルシューティング

- RSS提供元が全部失敗した／新着記事がない場合は、その日の公開を止め、架空の記事は作りません
- 生成AIはRSSのタイトル・抜粋に基づく要約です。原文全文との照合を保証するものではありません。元記事へのリンクから確認できます
- APIエラーの際はRSS見出しモードになり、番組冒頭に案内が入ります
- Actionsのスケジュール実行には遅延があり得ます。60日間活動のない公開リポジトリでは定期実行が無効になることがあります
- 実行に失敗した場合はActionsの赤い実行履歴を開いて失敗したステップを確認

## 内容の変更

- tools/auto_news.py：ニュースソース、話題の優先度、Gemini台本生成
- tools/speak_openjtalk.py：音声合成と字幕同期
- .github/workflows/daily-radio.yml：実行時刻、生成・公開
- station.json：局名やキャラクターなど
- episodes.json：自動生成した番組の一覧
- episodes/：公開台本。初期テンプレートのサンプルは一覧から除外

元の [myradioテンプレート](https://github.com/monoradio102/myradio) を使用しています。
プレーヤー・素材の詳細とライセンスは [LICENSE](LICENSE) と [docs/formats.md](docs/formats.md) を参照。

音声合成：Open JTalk / HTS Voice NIT ATR503 M001 © Nagoya Institute of Technology (HTS Working Group), CC BY 3.0。
