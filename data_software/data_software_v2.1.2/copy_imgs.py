import os
import shutil
from typing import List

def ch_ext(source, ext):
    base = source.split('.')[0]
    return base + ext

def copy_specific_files(source_dir: str, target_dir: str, source_json_dir: str, target_json_dir: str, file_names: List[str], overwrite: bool = False) -> None:
    """
    将指定目录中的特定文件复制到目标目录
    
    Args:
        source_dir (str): 源目录路径
        target_dir (str): 目标目录路径
        target_json_dir (str): 目标目录路径
        file_names (List[str]): 需要复制的文件名列表
        overwrite (bool): 是否覆盖已存在的文件，默认为False
    """
    # 确保目标目录存在
    os.makedirs(target_dir, exist_ok=True)
    os.makedirs(target_json_dir, exist_ok=True)
    
    copied_files = 0
    skipped_files = 0
    
    for file_name in file_names:
        # print(22, type(file_name), file_name)
        base_name = os.path.basename(file_name)
        source_path = os.path.join(source_dir, base_name)
        target_path = os.path.join(target_dir, base_name)

        source_json_path = os.path.join(source_json_dir, ch_ext(base_name, '.json'))
        target_json_path = os.path.join(target_json_dir, ch_ext(base_name, '.json'))
        
        if not os.path.exists(source_path):
            print(f"⚠️ 警告：源文件不存在 - {source_path}")
            skipped_files += 1
            continue
            
        if os.path.exists(target_path) and os.path.exists(target_json_path) and not overwrite:
            print(f"⏩ 跳过：文件已存在 - {target_path}")
            skipped_files += 1
            continue
            # 运输机
        try:
            if not os.path.exists(target_path):
                shutil.copy2(source_path, target_path)  # copy2会保留元数据
            shutil.copy2(source_json_path, target_json_path)  # copy2会保留元数据
            print(f"✅ 已复制：{source_json_path}")
            copied_files += 1
        except Exception as e:
            print(f"❌ 复制失败：{file_name} - {str(e)}")
            skipped_files += 1
    
    print("\n📊 复制结果：")
    print(f"成功复制文件: {copied_files}")
    print(f"跳过/失败文件: {skipped_files}")
    print(f"目标目录: {os.path.abspath(target_dir)}")

# 使用示例 元宝
# jb-aionlineinferenceservice-9091001526374703104
if __name__ == "__main__":
    # 配置参数
    SOURCE_DIR = "/path/to/source"      # 替换为你的源目录
    TARGET_DIR = "/path/to/destination" # 替换为目标目录
    FILES_TO_COPY = ["file1.txt", "image.jpg", "data.csv"]  # 要复制的文件名列表
    
    # 执行复制
    copy_specific_files(SOURCE_DIR, TARGET_DIR, FILES_TO_COPY, overwrite=True)