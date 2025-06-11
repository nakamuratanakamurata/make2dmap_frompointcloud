import os
import numpy as np
import pandas as pd

def clip_las_file(input_file, output_file, z_min, z_max):
    """
    LASファイルをZ座標でクリッピングする
    """
    try:
        import laspy
    except ImportError:
        print("Error: laspy library is required for LAS files.")
        print("Install with: pip install laspy")
        return False
    
    try:
        # LASファイルを読み込み
        with laspy.open(input_file) as f:
            las = f.read()
        
        print(f"Original points: {len(las.points)}")
        
        # Z座標でフィルタリング
        mask = (las.z >= z_min) & (las.z <= z_max)
        
        # フィルタリング後の点群を作成
        filtered_points = las.points[mask]
        
        print(f"Filtered points: {len(filtered_points)}")
        print(f"Removed points: {len(las.points) - len(filtered_points)}")
        
        # 新しいLASファイルを作成
        header = las.header
        header.point_count = len(filtered_points)
        
        with laspy.open(output_file, mode='w', header=header) as f:
            f.write_points(filtered_points)
        
        print(f"Successfully saved clipped LAS file: {output_file}")
        return True
        
    except Exception as e:
        print(f"Error processing LAS file: {e}")
        return False

def clip_txt_file(input_file, output_file, z_min, z_max, delimiter=' ', z_column=2):
    """
    TXTファイルをZ座標でクリッピングする
    
    Parameters:
    - input_file: 入力ファイルパス
    - output_file: 出力ファイルパス
    - z_min: Z座標の最小値
    - z_max: Z座標の最大値
    - delimiter: 区切り文字（デフォルト: スペース）
    - z_column: Z座標の列番号（0から開始、デフォルト: 2）
    """
    try:
        # TXTファイルを読み込み
        df = pd.read_csv(input_file, delimiter=delimiter, header=None)
        
        print(f"Original points: {len(df)}")
        
        # Z座標でフィルタリング
        filtered_df = df[(df.iloc[:, z_column] >= z_min) & (df.iloc[:, z_column] <= z_max)]
        
        print(f"Filtered points: {len(filtered_df)}")
        print(f"Removed points: {len(df) - len(filtered_df)}")
        
        # フィルタリング後のデータを保存
        filtered_df.to_csv(output_file, sep=delimiter, header=False, index=False)
        
        print(f"Successfully saved clipped TXT file: {output_file}")
        return True
        
    except Exception as e:
        print(f"Error processing TXT file: {e}")
        return False

def clip_point_cloud(input_file, output_file, z_min, z_max):
    """
    点群ファイルをZ座標でクリッピングする（LAS/TXT自動判定）
    
    Parameters:
    - input_file: 入力ファイルパス
    - output_file: 出力ファイルパス  
    - z_min: Z座標の最小値
    - z_max: Z座標の最大値
    """
    
    # ファイルの存在確認
    if not os.path.exists(input_file):
        print(f"Error: Input file '{input_file}' does not exist.")
        return False
    
    # ファイル拡張子で処理方法を判定
    file_ext = os.path.splitext(input_file)[1].lower()
    
    print(f"Processing file: {input_file}")
    print(f"Z-range filter: {z_min} <= Z <= {z_max}")
    print("-" * 50)
    
    if file_ext == '.las':
        return clip_las_file(input_file, output_file, z_min, z_max)
    elif file_ext in ['.txt', '.xyz', '.csv']:
        # TXTファイルの場合、区切り文字を自動判定
        delimiter = ' '
        if file_ext == '.csv':
            delimiter = ','
        elif file_ext == '.txt':
            # 最初の行をサンプリングして区切り文字を推定
            with open(input_file, 'r') as f:
                first_line = f.readline().strip()
                if ',' in first_line:
                    delimiter = ','
                elif '\t' in first_line:
                    delimiter = '\t'
                else:
                    delimiter = ' '
        
        return clip_txt_file(input_file, output_file, z_min, z_max, delimiter)
    else:
        print(f"Error: Unsupported file format '{file_ext}'. Supported formats: .las, .txt, .xyz, .csv")
        return False

# メイン処理
if __name__ == "__main__":
    # ===========================================
    # 設定パラメータ（ここを変更してください）
    # ===========================================
    
    # クリッピング範囲の設定
    Z_MIN = 4.8  # Z座標の最小値
    Z_MAX = 5.1  # Z座標の最大値
    
    # ファイルパスの設定
    INPUT_FILE = "output10000000.las"     # 入力ファイル
    OUTPUT_FILE = "output_clipped.las"    # 出力ファイル
    
    # ===========================================
    # 処理実行
    # ===========================================
    
    print("Point Cloud Z-Coordinate Clipping Tool")
    print("=" * 50)
    
    success = clip_point_cloud(INPUT_FILE, OUTPUT_FILE, Z_MIN, Z_MAX)
    
    if success:
        print("\n✓ Clipping completed successfully!")
    else:
        print("\n✗ Clipping failed!")
    
    print("=" * 50)

# 使用例:
# 
# 1. LASファイルの場合:
#    INPUT_FILE = "input.las"
#    OUTPUT_FILE = "output_clipped.las"
#
# 2. TXTファイルの場合:
#    INPUT_FILE = "input.txt"  # X Y Z形式
#    OUTPUT_FILE = "output_clipped.txt"
#
# 3. CSVファイルの場合:
#    INPUT_FILE = "input.csv"
#    OUTPUT_FILE = "output_clipped.csv"