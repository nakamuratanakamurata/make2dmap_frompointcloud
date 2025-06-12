# 点群データから2次元マップ作成マニュアル

## 1. 概要

本マニュアルでは、3次元点群データ（e57、LAS形式など）から、ロボットナビゲーション用の2次元マップ（PNG画像）を作成する手順を説明します。

### 1.1 処理の流れ
1. 点群データの前処理（変換とサブサンプリング）
2. 床面高さの特定
3. 2次元画像への投影
4. 手動での編集

## 2. 環境構築

### 2.1 ソフトウェア
- **CloudCompare**：点群の可視化と基本的な処理
- **LAStools**：LASファイルの処理とサブサンプリング(最近商用利用有料になった?)
- **E572LAS**：LAStoolsと同じ会社のソフトウェア
- **画像編集ソフト**：手動編集用（Photoshop、AffinityDesigner等）

### 2.2 python関連
- **pythonバージョン**：3.7以降
- **インストールするライブラリ**：


## 3. データ準備

### 3.1 元のデータ形式
e57形式を想定してドキュメントを書きます。
(他フォーマットでも問題なし)

### 3.2 データ変換
1. **e57ファイルの変換**
   - e572lasを使用してe57ファイルをlasに変換
下記リンクの一番最後のソフトフェア
https://rapidlasso.de/downloads/

   - matterportから出力したe57ファイルでも変換可
   基本的な使用方法
①exeファイルを実行し、e57ファイルをドラッグ&ドロップ
②コマンドラインで実行　(基本的にはe572lasのパスを通す必要あり)(パスが通ったら以下のリンクのように実行)
https://downloads.rapidlasso.de/html/e572las_README.html


2. **サブサンプリング**（大規模データの場合、必要であれば）
   *例）cloud compare CLI を使用した場合のコマンド
   ```bash
   CloudCompare -SILENT -O Shikatou_e572las.las -SS RANDOM 10000000 -C_EXPORT_FMT LAS -SAVE_CLOUDS FILE output10000000.las
   ```
   *　例）PDALを使用した場合のコマンド
   ```bash
   pdal translate input.las output.las --filters.sample.radius=1 --filters.sample.count=1
   ```
   - 0.01 = 1/100にサンプリング（22GB → 500MB程度）
   - (GUIで開くと、重い点群だとPCスペックによって大変)
   - (環境変数の設定でパスを通すのをお忘れなく(してない場合))

## 4. 処理手順

### 4.1 床面高さの特定

1. **CloudCompareでの確認**
   - LASファイルを読み込み (サブサンプリングした点群がよいかと)
   - 床面と思われる部分の点をピックアップ
   - 床面のZ座標の相場を把握
![Image](https://github.com/user-attachments/assets/c61da330-5f68-46cc-a6c0-16757d92cc18)

![Image](https://github.com/user-attachments/assets/bab417bd-597b-4bb8-ac32-becfed3755f8)

2. **床面高さの決定**
   - 例：1階 z = 0.02m程度
   - 例：2階 z = 0m程度（ほぼゼロ）
   - **注意**：床面は完全に平坦ではない場合が多い

### 4.2 参照高さ範囲の決定

1. **2D LiDARの高さを考慮**
   - SLAM用マップの場合：床面 + 177.4mm（LiDAR設置高さ）
   - 一般的な設定：床面から10cm〜50cm（または70cm）の範囲

2. **高さ範囲の切り出し**
   ```bash
   # las2las_clip.batの例
   las2las -i input.las -o output_clipped.las -keep_z 0.1 0.7
   ```

### 4.3 2次元画像への投影

1. **基本的な投影処理**（txt2png.py）
   - 点群のX,Y座標を画像のピクセル座標に変換
   - ピクセルサイズ：0.05m（5cm）を推奨
   - 白背景に黒点として描画

2. **ノイズ除去を含む投影処理**（txt2png_30over.py）
   - 各ピクセルに30個以上の点がある場合のみ黒く塗る
   - ノイズやポールパーテーションなどの一時的な障害物を除外

3. **点の密度を可視化**（txt2png_count.py）
   - 0-4個：薄い色
   - 5-9個：中間色
   - 10-19個：濃い色
   - 20-29個：最も濃い色
   - 床面の連続性を確認するのに有用

### 4.4 手動編集

1. **編集が必要な箇所**
   - ノイズの除去
   - 壁の接続部分の修正
   - 未知領域（灰色）の追加
   - ポールパーテーション等の可動物の除去

2. **編集時の注意点**
   - NavigationStackの要件：5cm四方のグリッドを意識
   - 壁や固定障害物は確実に黒く塗る
   - 通行可能な領域は白のまま残す

## 5. パラメータ設定

### 5.1 重要なパラメータ

| パラメータ | 推奨値 | 説明 |
|---------|-------|------|
| ピクセルサイズ | 0.05m | マップの解像度（5cm/pixel） |
| 参照高さ（下限） | 床面+0.1m | 床面ノイズを除外 |
| 参照高さ（上限） | 床面+0.5〜0.7m | 椅子等の障害物を含む |
| 点数閾値 | 30個 | ノイズ除去の基準 |

### 5.2 複数階層の処理
- 各階で床面高さが異なるため、個別に処理
- 最後に適切な位置関係でマージ
- **注意**：階層間で1m程度のずれが生じる場合がある

## 6. トラブルシューティング

### 6.1 よくある問題

**Q: ファイルが開けない**
- A: メモリ不足の可能性。サブサンプリングを実施

**Q: 床面にノイズが多い**
- A: 参照高さの下限を上げる（例：0.1m → 0.15m）

**Q: 椅子などが認識されない**
- A: 参照高さの上限を上げる（例：0.5m → 0.7m）

**Q: マップに穴が空いている**
- A: 点数閾値を下げるか、手動で編集

### 6.2 スキャン誤差の対処
- 複数階層や広範囲のスキャンでは位置ずれが発生
- 手動で位置合わせが必要な場合がある

## 7. プログラムの使用方法

### 7.1 基本的な実行方法
```bash
# 点群データをテキスト形式で準備（X,Y,Z形式）
# CloudCompareでASCII形式でエクスポート

# 基本的な2D画像生成
python txt2png.py input_points.txt

# ノイズ除去を含む生成
python txt2png_30over.py input_points.txt

# 点密度の可視化
python txt2png_count.py input_points.txt

# 背景を透過に変換
python make_transparent_png.py input.png output.png
```

### 7.2 GitHubリポジトリ構成（予定）
```
pointcloud-to-map/
├── README.md
├── clip.py
├── point2png.py
├── point2png_over_threshold.py
├── point2png_count.py
└── make_transparent_png.py 

```

## 8. 参考情報

- NavigationStack要件：[robo-marc.github.io](https://robo-marc.github.io/navigation_documents/navigation_overview.html)
- 推奨マップ解像度：5cm/pixel（50cm四方ではなく5cm四方）
- マップ形式：PNG（白：通行可能、黒：障害物、灰色：未知領域）

## 9. 注意事項

- 大規模な点群データは処理に時間がかかるため、適切なサブサンプリングを実施
- 手動編集は必須の工程として計画に含める
- 可動物（ポールパーテーション等）は除外する
- 階層間の位置合わせは慎重に行う
