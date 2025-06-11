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
            x, y = map(float, parts[:2])  # 最初の2つの要素（x, y）を取得
            coordinates.append((x, y))
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
    point_color = tuple(config['colors']['point_color'])
    
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

    # 座標をピクセルに変換して描画
    for x, y in coordinates:
        px = int((x - min_x) / pixel_size)
        py = int((y - min_y) / pixel_size)
        # 画像範囲内かチェック
        if 0 <= px < width and 0 <= py < height:
            pixels[px, py] = point_color

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
    output_file_name = config['output_files']['point2png_output']
    image.save(output_file_name)
    print(f"Image saved as {output_file_name}")

if __name__ == "__main__":
    main()