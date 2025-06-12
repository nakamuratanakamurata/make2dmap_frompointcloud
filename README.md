# 点群データから2次元マップ作成マニュアル

## 1. 概要

本マニュアルでは、3次元点群データ（e57、LAS形式など）から、
ロボットナビゲーション用の2次元マップ（PNG画像）を作成する手順を説明します。

### 1.1 処理の流れ
1. 点群データの前処理（変換とサブサンプリング）
2. 床面高さの特定
3. 2次元画像への投影
4. 手動編集

## 2. 環境構築

### 2.1 おすすめソフトウェア
どのソフトウェアで前処理等を行っても構いません。あくまでおすすめ。
- **CloudCompare**：床の点群のZ座標を把握するのにGUIでの操作が良いかと
- **LAStools**：LASファイルの処理とサブサンプリング(最近商用利用有料になった?)
- **E572LAS**：LAStoolsと同じ会社のソフトウェア
https://rapidlasso.de/downloads/
- **PDAL**：コマンドで点群の処理がしやすい
- **画像編集ソフト**：手動編集用（Photoshop、AffinityDesigner等）

### 2.2 python関連
- **Python要件：Python 3.11以降推奨（tomllib標準ライブラリのため）
- **インストールするライブラリ**：
   ```bash
   pip install numpy pandas pillow laspy
   ```
※Python 3.10以前の場合はtomliライブラリが追加で必要

## 3. 処理1 点群データの前処理

e57形式を想定してドキュメントを書きます。
(他フォーマットでも問題なし)

1. **e57ファイルの変換**
   - e572lasを使用してe57ファイルをlasに変換
     (matterportから出力したe57ファイルでも変換可)
     e572lasの基本的な使用方法(以下の2種類のどちらでも)
     ①exeファイルを実行し、e57ファイルをドラッグ&ドロップ
     ②コマンドラインで実行　(基本的にe572lasのパスを通す必要あり)(パスが通ったら以下リンクのように実行)
     https://downloads.rapidlasso.de/html/e572las_README.html


2. **サブサンプリング**（大規模データの場合、必要であれば）

   *　例）cloud compare CLI を使用した場合のコマンド
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

## 4. 処理2 床面高さの特定

1. **CloudCompareで確認**
   - LASファイルを読み込み (サブサンプリングした点群がよいかと)
   - 床面と思われる部分の点をピックアップ
   - 床面のZ座標の相場を把握
![Image](https://github.com/user-attachments/assets/c61da330-5f68-46cc-a6c0-16757d92cc18)

![Image](https://github.com/user-attachments/assets/bab417bd-597b-4bb8-ac32-becfed3755f8)

2. **床面高さの決定**
   - 例：1階床 z = 0.02~0.05程度
   - **注意**：床面は完全に平坦ではない場合がある
  
   - ロボット等の自動走行をする場合、lidarを設置する高さを考慮:
     床面高さ+LiDAR設置高さ
     例) 0.03m + 0.2m 

3. **高さ範囲の切り出し**
   切り出す高さはノイズを低減するために数十cm程の範囲を持たせたほうが安定する気がします。0.2~0.4等
   ```bash
   # clip.pyの例
   # パラメータはconfig.tomlにて設定 (zの値の範囲)
   python clip.py

   # las2lasの例
   las2las -i input.las -o output_clipped.las -keep_z 0.2 0.4
   ```
## 5. 処理3 2次元画像への投影
以下の3つのプログラムの出力をそれぞれ参照しながら2Dマップを作成すると良いかと思います。

1. **基本的な投影処理**（txt2png.py）
   - 点群のX,Y座標を画像のピクセル座標に変換
   - ピクセルサイズ：0.05m（5cm）を推奨
   - 白背景に黒点として描画

2. **ノイズ除去を含む投影処理**（txt2png_over_threshold.py）
config.tomlにてしきい値を設定。
   - 各ピクセルにthreshold個以上の点がある場合のみ黒く塗る
   - ノイズやポールパーテーションなどの一時的な障害物を除外したい際などに有効

3. **点の密度を可視化**（txt2png_count.py）
点密度ごとに色分け
config.tomlにて、点の個数の範囲、色が変更可能。
   - 0-4個：薄い色
   - 5-9個：中間色
   - 10-19個：濃い色
   - 20-29個：最も濃い色
   - 床面の連続性を確認するのに有用


## 6. 処理4 手動編集
txt2png.py or txt2png_over_threshold.py で出力した黒のpngファイルをベースに、手動で編集。
make_transparent_png.py で、他のpng画像を半透明にして画像編集ソフトで重ね合わせつつ編集すると楽です。

1. **編集が必要な箇所**
   - ノイズの除去
   - 壁の接続部分の修正
   - 未知領域（灰色）の追加
   - ポールパーテーション等の移動可能な物の除去

2. **編集時の注意点**
   - NavigationStackの要件：5cm四方のグリッドを意識
   - 壁や固定障害物は確実に黒く塗る
   - 通行可能な領域は白のまま残す

## 7. プログラム

### 7.1 基本的な実行方法
```bash
# 指定した高さの範囲の点群のみ切り抜き
python clip.py

# 基本的な2D画像生成
python point2png.py

# ノイズ除去を含む生成
python point2png_over_threshold.py

# 点密度の可視化
python point2png_count.py

# 白背景のpngファイルの背景を透過に変換　(要:実行時引数)
python make_transparent_png.py input.png output.png
```

### 7.2 GitHubリポジトリ構成
```
make2dmap/
├── README.md
├── clip.py
├── config.toml
├── make_transparent_png.py
├── point2png.py
├── point2png_count.py
└── point2png_over_threshold.py

```

## 8. パラメータ設定 config.toml について



## 9. 参考情報

- NavigationStack要件：[robo-marc.github.io](https://robo-marc.github.io/navigation_documents/navigation_overview.html)
- 推奨マップ解像度：5cm/pixel（50cm四方ではなく5cm四方）
- マップ形式：PNG（白：通行可能、黒：障害物、灰色：未知領域）
