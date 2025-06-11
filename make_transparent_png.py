import sys
from PIL import Image

def make_transparent(png_file_path):
    # 画像を読み込む
    with Image.open(png_file_path) as img:
        img = img.convert("RGBA")  # RGBAモードに変換
        datas = img.getdata()

        newData = []
        for item in datas:
            # RGBが(255, 255, 255)のピクセルを透過させる
            if item[0] == 255 and item[1] == 255 and item[2] == 255:
                newData.append((255, 255, 255, 0))
            else:
                newData.append(item)

        img.putdata(newData)

        # 新しいファイル名を作成
        new_file_path = png_file_path.rsplit('.', 1)[0] + '_transparent.png'
        img.save(new_file_path, "PNG")
        print(f"Saved transparent image as {new_file_path}")

def main():
    if len(sys.argv) != 2:
        print("Usage: python make_transparent_png.py <path_to_png_file>")
        sys.exit(1)

    png_file_path = sys.argv[1]
    make_transparent(png_file_path)

if __name__ == "__main__":
    main()
