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
- **Python要件**：Python 3.11以降推奨（tomllib標準ライブラリのため）
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

1. **基本的な投影処理**（point2png.py）
   - 点群のX,Y座標を画像のピクセル座標に変換
   - ピクセルサイズ：0.05m（5cm）を推奨
   - 白背景に黒点として描画

2. **ノイズ除去を含む投影処理**（point2png_over_threshold.py）
config.tomlにてしきい値を設定。
   - 各ピクセルにthreshold個以上の点がある場合のみ黒く塗る
   - ノイズやポールパーテーションなどの一時的な障害物を除外したい際などに有効

4. **点の密度を可視化**（point2png_count.py）
点密度ごとに色分け
config.tomlにて、点の個数の範囲、色が変更可能。
   - 0-4個：薄い色
   - 5-9個：中間色
   - 10-19個：濃い色
   - 20-29個：最も濃い色
   - 床面の連続性を確認するのに有用

## 6. 処理4 手動編集
point2png.py または point2png_over_threshold.py で出力した黒のpngファイルをベースに、手動で編集。
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
├── environments.txt
├── make_transparent_png.py
├── point2png.py
├── point2png_count.py
└── point2png_over_threshold.py
```

## 8. パラメータ設定 config.toml について

プログラムの動作はconfig.tomlファイルで制御されます。まず全体の設定ファイルを示し、その後各プログラムでの設定ポイントを説明します。

### 8.1 config.toml 全体
```toml
[general]
# 全プログラム共通設定
pixel_size = 0.05
background_color = "white"
output_format = "png"

[input_files]
# 全プログラム共通の入力ファイルパス
input_file = "data/sample.txt"  # txtファイルでもlasファイルでも共通

[output_files]
# 各プログラムの出力ファイル名設定
point2png_output = "output.png"
point2png_over_threshold_output = "output_threshold.png"
point2png_count_output = "output_count.png"
clip_output = "output_clipped"  # 拡張子は入力ファイルと同じになります

[clip]
# clip.py専用設定
z_min = 4.8
z_max = 5.1
z_column = 2  # Z座標の列番号（0から開始）

[data_format]
# 全プログラム共通: 空白区切りファイル
delimiter = "space"
coordinate_columns = 3  # x, y, z の3列（zは無視、txt2png.pyではx,yのみ使用）

[colors]
# 全プログラム共通
point_color = [0, 0, 0]  # 黒色 (R,G,B)

# point2png_over_threshold.py専用: 閾値による色分け
threshold_count = 20
below_threshold_color = [255, 255, 255]  # 白色
above_threshold_color = [0, 0, 0]        # 黒色

# point2png_count.py専用: カウント範囲による色分け
count_range_1_max = 5
count_range_1_color = [255, 0, 0]    # 赤色

count_range_2_min = 5
count_range_2_max = 10
count_range_2_color = [0, 0, 255]    # 青色

count_range_3_min = 10
count_range_3_max = 20
count_range_3_color = [0, 255, 0]    # 緑色

count_range_4_min = 20
count_range_4_max = 30
count_range_4_color = [100, 0, 100]  # 紫色

count_range_5_min = 30
count_range_5_color = [0, 0, 0]      # 黒色
```

### 8.2 python clip.py での設定ポイント

**必ず調整するパラメータ**:
```toml
[input_files]
input_file = "input.las"  # 処理したいLAS/TXTファイルのパスに変更

[output_files]
clip_output = "output.las"  # 出力ファイル名を指定

[clip]
z_min = 0.2  # 抽出する高さの下限
z_max = 0.4  # 抽出する高さの上限
z_column = 2 # TXTファイルの場合のZ座標列番号 (x:0,y:1,z:2がデフォかと)

```

### 8.3 python point2png.py での設定ポイント

**必ず変更するパラメータ**:
```toml
[input_files]
input_file = "output_clipped.las"  # 通常はclip.pyの出力ファイル

[output_files]
point2png_output = "basic_map.png"  # 出力画像ファイル名
```

**必要な場合に調整するパラメータ**:
```toml
[general]
pixel_size = 0.05  # 1ピクセルあたりの実寸法（メートル）

[colors]
point_color = [0, 0, 0]  # 点の色（RGB）
```

**pixel_size**の調整: 0.05 (5cm)が推奨設定。0.02 (2cm)で高解像度、0.1 (10cm)で処理速度重視。

### 8.4 python point2png_over_threshold.py での設定ポイント

**必ず変更するパラメータ**:
```toml
[input_files]
input_file = "output_clipped.las"  # 通常はclip.pyの出力ファイル

[output_files]
point2png_over_threshold_output = "threshold_map.png"  # 出力画像ファイル名

[colors]
threshold_count = 20              # 閾値（最重要）
```

**必要な場合に調整するパラメータ**:
```toml
[colors]
below_threshold_color = [255, 255, 255]  # 閾値未満の色
above_threshold_color = [0, 0, 0]        # 閾値以上の色
```

**threshold_count**の調整: 5-10で軽いノイズ除去、20-30で標準設定、50以上で強いノイズ除去。屋内環境では20-30程度、屋外環境では30-50程度が目安。

### 8.5 python point2png_count.py での設定ポイント

**必ず変更するパラメータ**:
```toml
[input_files]
input_file = "output_clipped.las"  # 通常はclip.pyの出力ファイル

[output_files]
point2png_count_output = "density_map.png"  # 出力画像ファイル名
```

**必要な場合に調整するパラメータ**:
```toml
[colors]
count_range_1_max = 5
count_range_1_color = [255, 0, 0]    # 1-4個の点（赤）

count_range_2_min = 5
count_range_2_max = 10  
count_range_2_color = [0, 0, 255]    # 5-9個の点（青）

count_range_3_min = 10
count_range_3_max = 20
count_range_3_color = [0, 255, 0]    # 10-19個の点（緑）

count_range_4_min = 20
count_range_4_max = 30
count_range_4_color = [100, 0, 100]  # 20-29個の点（紫）

count_range_5_min = 30
count_range_5_color = [0, 0, 0]      # 30個以上（黒）
```

範囲の調整: データの密度に応じてレンジを変更。点群が密な場合は各レンジを大きく、疎な場合は小さく設定。このプログラムは点密度の分布確認と閾値設定の参考に使用。


## 9. 参考情報

- NavigationStack要件：[robo-marc.github.io](https://robo-marc.github.io/navigation_documents/navigation_overview.html)
- 推奨マップ解像度：5cm/pixel（50cm四方ではなく5cm四方）
- マップ形式：PNG（白：通行可能、黒：障害物、灰色：未知領域）
