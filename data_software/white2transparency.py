from PIL import Image

def white_to_transparency(input_path, output_path, threshold=230):
    """
    将PNG图片的白色背景转换为透明背景
    
    参数:
    input_path (str): 输入图片路径
    output_path (str): 输出图片路径
    threshold (int): 白色阈值 (0-255)，默认为230
    """
    # 打开图片并转换为RGBA模式
    img = Image.open(input_path)
    img = img.convert("RGBA")
    
    # 获取图片数据
    data = img.getdata()
    
    # 创建新数据列表
    new_data = []
    for item in data:
        # 如果RGB值都大于阈值，则设为透明
        if item[0] > threshold and item[1] > threshold and item[2] > threshold:
            new_data.append((255, 255, 255, 0))  # 全透明
        else:
            new_data.append(item)  # 保留原像素
    
    # 更新图片数据并保存
    img.putdata(new_data)
    img.save(output_path, "PNG")

# 使用示例
if __name__ == "__main__":
    input_image = "CASC-LOGO.png"   # 输入图片路径
    output_image = "CASC-LOGO-transparency.png" # 输出图片路径
    
    white_to_transparency(input_image, output_image)
    
    print(f"转换完成！已保存为: {output_image}")
