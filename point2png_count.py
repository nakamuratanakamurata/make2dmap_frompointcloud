import sys
import numpy as np
import os
import tomllib
from PIL import Image

def load_config():
    with open('config.toml', 'rb') as f:
        config = tomllib.load(f)
    return config

def load_coordinates_from_txt(file_path):
    """TXTファイルからx,y座標を読み込む"""
    with open(file_path, 'r') as file:
        coordinates = []
        for line in file:
            parts = line.strip().split()  # 空白で分割
            x, y, z = map(float, parts[:3])  # 最初の3つの要素（x, y, z）を取得
            coordinates.append((x, y))  # z座標は無視
    return coordinates

def load_coordinates_from_las(file_path):
    """LASファイルからx,y座標を読み込む"""
    import laspy
    
    with laspy.open(file_path) as las_file:
        las_data = las_file.read()
        # x, y座標を取得（z座標は無視）
        x_coords = las_data.x
        y_coords = las_data.y
        
        # タプルのリストに変換
        coordinates = [(float(x), float(y)) for x, y in zip(x_coords, y_coords)]
        
    print(f"Loaded {len(coordinates)} points from LAS file")
    return coordinates

def load_coordinates(file_path):
    """ファイル形式を自動判定して座標を読み込む"""
    file_ext = os.path.splitext(file_path)[1].lower()
    
    if file_ext == '.las':
        return load_coordinates_from_las(file_path)
    elif file_ext in ['.txt', '.xyz', '.csv']:
        return load_coordinates_from_txt(file_path)
    else:
        raise ValueError(f"Unsupported file format: {file_ext}")

def create_image(coordinates, config):
    pixel_size = config['general']['pixel_size']
    background_color = config['general']['background_color']
    
    # カウント範囲の設定を読み込み
    colors_config = config['colors']
    range_1_max = colors_config['count_range_1_max']
    range_1_color = tuple(colors_config['count_range_1_color'])
    
    range_2_min = colors_config['count_range_2_min']
    range_2_max = colors_config['count_range_2_max']
    range_2_color = tuple(colors_config['count_range_2_color'])
    
    range_3_min = colors_config['count_range_3_min']
    range_3_max = colors_config['count_range_3_max']
    range_3_color = tuple(colors_config['count_range_3_color'])
    
    range_4_min = colors_config['count_range_4_min']
    range_4_max = colors_config['count_range_4_max']
    range_4_color = tuple(colors_config['count_range_4_color'])
    
    range_5_min = colors_config['count_range_5_min']
    range_5_color = tuple(colors_config['count_range_5_color'])
    
    # 座標の範囲を取得
    min_x = min(coordinates, key=lambda x: x[0])[0]
    max_x = max(coordinates, key=lambda x: x[0])[0]
    min_y = min(coordinates, key=lambda x: x[1])[1]
    max_y = max(coordinates, key=lambda x: x[1])[1]

    print(f"Coordinate range: X({min_x:.2f}, {max_x:.2f}), Y({min_y:.2f}, {max_y:.2f})")

    # 画像のサイズを計算
    width = int((max_x - min_x) / pixel_size) + 1
    height = int((max_y - min_y) / pixel_size) + 1

    print(f"Image size: {width} x {height} pixels")

    # 白い背景で画像を初期化
    image = Image.new('RGB', (width, height), background_color)
    pixels = image.load()

    # 各ピクセルのカウントを格納する辞書
    pixel_counts = {}

    # 座標をピクセルに変換してカウント
    for x, y in coordinates:
        px = int((x - min_x) / pixel_size)
        py = int((y - min_y) / pixel_size)
        # 画像範囲内かチェック
        if 0 <= px < width and 0 <= py < height:
            if (px, py) not in pixel_counts:
                pixel_counts[(px, py)] = 0
            pixel_counts[(px, py)] += 1

    # カウントに基づいて色を塗る
    color_counts = {
        'range_1': 0, 'range_2': 0, 'range_3': 0, 'range_4': 0, 'range_5': 0
    }
    
    for (px, py), count in pixel_counts.items():
        if count < range_1_max:
            color = range_1_color
            color_counts['range_1'] += 1
        elif range_2_min <= count < range_2_max:
            color = range_2_color
            color_counts['range_2'] += 1
        elif range_3_min <= count < range_3_max:
            color = range_3_color
            color_counts['range_3'] += 1
        elif range_4_min <= count < range_4_max:
            color = range_4_color
            color_counts['range_4'] += 1
        else:  # count >= range_5_min
            color = range_5_color
            color_counts['range_5'] += 1
        pixels[px, py] = color

    # 統計情報を表示
    print(f"Total pixels with points: {len(pixel_counts)}")
    print(f"Count distribution:")
    print(f"  Range 1 (< {range_1_max}): {color_counts['range_1']} pixels")
    print(f"  Range 2 ({range_2_min}-{range_2_max-1}): {color_counts['range_2']} pixels")
    print(f"  Range 3 ({range_3_min}-{range_3_max-1}): {color_counts['range_3']} pixels")
    print(f"  Range 4 ({range_4_min}-{range_4_max-1}): {color_counts['range_4']} pixels")
    print(f"  Range 5 (>= {range_5_min}): {color_counts['range_5']} pixels")

    return image

def main():
    # 設定ファイル読み込み
    config = load_config()

    # コマンドライン引数があればそれを使用、なければ設定ファイルから読み込み
    if len(sys.argv) == 2:
        file_path = sys.argv[1]
    else:
        file_path = config['input_files']['input_file']
        print(f"Using input file from config: {file_path}")

    # ファイル存在チェック
    if not os.path.exists(file_path):
        print(f"Error: Input file '{file_path}' not found")
        sys.exit(1)

    coordinates = load_coordinates(file_path)

    image = create_image(coordinates, config)

    # 出力ファイル名を設定ファイルから取得
    output_file_name = config['output_files']['point2png_count_output']
    image.save(output_file_name)
    print(f"Image saved as {output_file_name}")

if __name__ == "__main__":
    main()