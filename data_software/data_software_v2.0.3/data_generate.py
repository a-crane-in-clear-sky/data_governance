import os
import json
import io
import re
from tqdm import tqdm
from openai import OpenAI
import requests
import base64
from PIL import Image
from openai import BadRequestError
import shutil
import sys
import argparse
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
                             QPushButton, QTextEdit, QApplication, QFileDialog)
from PyQt5.QtCore import Qt

def remove_markdown(text):
    text = re.sub(r'^#+\s*', '', text, flags=re.MULTILINE)
    text = re.sub(r'[\*\_]{1,2}(.*?)[\*\_]{1,2}', r'\1', text)
    text = re.sub(r'^[\-\*\+]\s*', '', text, flags=re.MULTILINE)
    text = re.sub(r'\n\s*\n', '\n\n', text).strip()
    return text

def encode_image_to_base64(image_path):
    with Image.open(image_path) as img:
        buffered = io.BytesIO()
        img.save(buffered, format=img.format)
        img_byte = buffered.getvalue()
    return base64.b64encode(img_byte).decode('utf-8')

def parse_and_save_to_json(text, output_file):
    result = {"CAP": "", "Q": "", "A": ""}
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        cap_match = re.search(r'"描述":\s*"([^"]*)"', text)
        q_match = re.search(r'"问题":\s*"([^"]*)"', text)
        a_match = re.search(r'"回答":\s*"([^"]*)"', text)
        if cap_match: result["CAP"] = cap_match.group(1)
        if q_match: result["Q"] = q_match.group(1)
        if a_match: result["A"] = a_match.group(1)
    else:
        if "描述" in data: result["CAP"] = data["描述"]
        if "问答" in data and data["问答"]:
            if "问题" in data["问答"][0]: result["Q"] = data["问答"][0]["问题"]
            if "回答" in data["问答"][0]: result["A"] = data["问答"][0]["回答"]
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    return result

def read_json_as_text(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            json_data = json.load(file)
            return json.dumps(json_data, ensure_ascii=False, indent=2)
    except Exception:
        return None

def run_in_command_line(chunk, chunk_num, img_dir, coco_label_dir):
    """命令行模式下运行数据处理"""
    print(f"开始处理: chunk={chunk}, chunk_num={chunk_num}")
    print(f"图像文件夹: {img_dir}")
    print(f"标签文件夹: {coco_label_dir}")
    
    # 初始化客户端
    client = OpenAI(
        base_url="http://localhost:8089/v1",
        api_key="no-api-key-required"
    )
    
    out_img_dir = "./images_new/"
    os.makedirs(out_img_dir, exist_ok=True)
    img_files = [f for f in os.listdir(img_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tif', '.tiff'))]
    img_files.sort()
    
    Len = len(img_files)
    chunk_size = Len // chunk_num
    img_files2proc = img_files[chunk*chunk_size: (chunk+1)*chunk_size] if chunk != chunk_num - 1 else img_files[chunk*chunk_size:]
    
    print(f"图像总数: {Len}, 当前处理: {len(img_files2proc)}张")
    
    prompt = (
        "请基于输入的图像和COCO格式的标签json文件给出以下内容，使用json格式。"
        "第一段详细描述这张图像的内容，主要包括物体、场景、颜色、动作和物体间的相互关系等元素。要求描述细致准确，统计物体数据要精确，重点关注军事情报相关信息；"
        "第二段根据图像内容只生成一个高质量的问答对，这一个问答对针对的是图像中目标的动作意图。使用格式：Q: [问题] \nA: [答案]。问答对应当是信息密度较高的，且答案应当准确而完整。"
        "这两段话封装在如下json结构体内：{'描述': 'xxx', '问答': [{'问题': 'xxx', '回答': 'xxx'}]}"
    )
    
    output_json_path = "./output_sar_show/"
    os.makedirs(output_json_path, exist_ok=True)
    
    for img_file in tqdm(img_files2proc):
        try:
            json_path = os.path.splitext(img_file)[0] + ".json"
            coco_path = os.path.join(coco_label_dir, os.path.basename(json_path))
            json_out_path = os.path.join(output_json_path, os.path.basename(json_path))
            
            if os.path.exists(json_out_path):
                print(f"跳过已处理文件: {img_file}")
                continue
            
            coco_text = read_json_as_text(coco_path)
            prompt_temp = prompt + "\n以下是该张图片的coco格式标注：\n" + (coco_text if coco_text else "")
            img_path = os.path.join(img_dir, img_file)
            
            # 处理图像
            print(f"处理中: {img_file}")
            image_base64 = encode_image_to_base64(img_path)
            response = client.chat.completions.create(
                model="InternVL3-8B",
                messages=[
                    {"role": "system", "content": "你是一个专业的遥感视觉助手，可以分析和回答关于图像的问题。能够全面、详细地描述影像中所有的目标类型、目标数量、目标位置（左上、上部、右上、左部、中部、右部、左下、下部、右下），目标类型包括战车、坦克、汽车、火车、战术小队等陆地目标，航空母舰、巡洋舰、驱逐舰、护卫舰、舰艇、潜艇等海上目标，战斗机、轰炸机、运输机、直升机等空中目标，以及机场、港口、油库、油罐等设施目标，以及图中能够识别到的其他设施及数量，如图中没有出现可不进行描述。输出一段完整的文字描述，包含上述信息，不要生成MarkDown格式。"},
                    {"role": "user", "content": [
                        {"type": "text", "text": prompt_temp},
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_base64}"}}
                    ]}
                ],
                max_tokens=30000,
                stream=False
            )
            generated_text = response.choices[0].message.content
            generated_text = remove_markdown(generated_text)
            
            parse_and_save_to_json(generated_text, json_out_path)
            img_out_path = os.path.join(out_img_dir, img_file)
            shutil.copy(img_path, img_out_path)
            
            print(f"完成: {img_file}")
        except BadRequestError as e:
            print(f"处理错误 - 跳过: {img_file} - {str(e)}")
        except Exception as e:
            print(f"未知错误 - 跳过: {img_file} - {str(e)}")
    
    print("数据处理完成!")

class DataGenerator(QWidget):
    def __init__(self):
        super().__init__()
        # 默认路径
        self.img_dir = "./sar_dataset/tif/"
        self.coco_label_dir = "./sar_dataset/json/"
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # 标题
        title = QLabel("数据制备")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("""
            font-size: 24px; 
            font-weight: bold; 
            color: #00ffff;
            padding: 10px;
        """)
        layout.addWidget(title)
        
        # 文件夹选择部分
        folder_layout = QVBoxLayout()
        
        # 图像文件夹选择
        img_folder_layout = QHBoxLayout()
        img_folder_layout.addWidget(QLabel("图像文件夹:"))
        self.img_dir_input = QLineEdit(self.img_dir)
        self.img_dir_input.setStyleSheet("background-color: rgba(30, 40, 60, 0.8); color: white;")
        self.img_dir_input.setReadOnly(True)
        img_folder_layout.addWidget(self.img_dir_input, 4)
        
        self.img_dir_btn = QPushButton("选择...")
        self.img_dir_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(30, 144, 255, 0.5);
                color: white;
                border: 1px solid #00ffff;
                border-radius: 5px;
                padding: 5px 10px;
            }
            QPushButton:hover {
                background-color: rgba(30, 144, 255, 0.8);
            }
        """)
        self.img_dir_btn.setMaximumWidth(80)
        self.img_dir_btn.clicked.connect(self.select_img_dir)
        img_folder_layout.addWidget(self.img_dir_btn, 1)
        folder_layout.addLayout(img_folder_layout)
        
        # 标签文件夹选择
        label_folder_layout = QHBoxLayout()
        label_folder_layout.addWidget(QLabel("标签文件夹:"))
        self.coco_dir_input = QLineEdit(self.coco_label_dir)
        self.coco_dir_input.setStyleSheet("background-color: rgba(30, 40, 60, 0.8); color: white;")
        self.coco_dir_input.setReadOnly(True)
        label_folder_layout.addWidget(self.coco_dir_input, 4)
        
        self.coco_dir_btn = QPushButton("选择...")
        self.coco_dir_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(30, 144, 255, 0.5);
                color: white;
                border: 1px solid #00ffff;
                border-radius: 5px;
                padding: 5px 10px;
            }
            QPushButton:hover {
                background-color: rgba(30, 144, 255, 0.8);
            }
        """)
        self.coco_dir_btn.setMaximumWidth(80)
        self.coco_dir_btn.clicked.connect(self.select_coco_dir)
        label_folder_layout.addWidget(self.coco_dir_btn, 1)
        folder_layout.addLayout(label_folder_layout)
        
        layout.addLayout(folder_layout)
        
        # 参数输入
        params_layout = QVBoxLayout()
        params_layout.addWidget(QLabel("处理参数"))
        
        # Chunk 输入
        chunk_layout = QHBoxLayout()
        chunk_layout.addWidget(QLabel("Chunk:"))
        self.chunk_input = QLineEdit("0")
        self.chunk_input.setStyleSheet("background-color: rgba(30, 40, 60, 0.8); color: white;")
        chunk_layout.addWidget(self.chunk_input)
        params_layout.addLayout(chunk_layout)
        
        # Chunk Num 输入
        chunk_num_layout = QHBoxLayout()
        chunk_num_layout.addWidget(QLabel("Chunk Num:"))
        self.chunk_num_input = QLineEdit("5")
        self.chunk_num_input.setStyleSheet("background-color: rgba(30, 40, 60, 0.8); color: white;")
        chunk_num_layout.addWidget(self.chunk_num_input)
        params_layout.addLayout(chunk_num_layout)
        
        layout.addLayout(params_layout)
        
        # 日志输出
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setStyleSheet("""
            background-color: rgba(10, 20, 35, 0.8); 
            color: #e0f0ff; 
            border: 1px solid #1e90ff;
            font-size: 14px;
        """)
        layout.addWidget(QLabel("处理日志:"))
        layout.addWidget(self.log_output)
        
        # 开始按钮
        self.start_btn = QPushButton("开始数据制备")
        self.start_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(30, 144, 255, 0.5);
                color: white;
                border: 1px solid #00ffff;
                border-radius: 5px;
                padding: 10px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(30, 144, 255, 0.8);
            }
        """)
        self.start_btn.clicked.connect(self.start_generation)
        layout.addWidget(self.start_btn)
        
        layout.addStretch()
    
    def select_img_dir(self):
        """选择图像文件夹"""
        folder = QFileDialog.getExistingDirectory(self, "选择图像文件夹", self.img_dir)
        if folder:
            self.img_dir = folder
            self.img_dir_input.setText(folder)
            self.log_message(f"图像文件夹设置为: {folder}")
    
    def select_coco_dir(self):
        """选择标签文件夹"""
        folder = QFileDialog.getExistingDirectory(self, "选择标签文件夹", self.coco_label_dir)
        if folder:
            self.coco_label_dir = folder
            self.coco_dir_input.setText(folder)
            self.log_message(f"标签文件夹设置为: {folder}")
    
    def log_message(self, message):
        """向日志区域添加消息"""
        self.log_output.append(message)
        QApplication.processEvents()
    
    def start_generation(self):
        """启动数据处理流程"""
        try:
            chunk = int(self.chunk_input.text())
            chunk_num = int(self.chunk_num_input.text())
            img_dir = self.img_dir
            coco_label_dir = self.coco_label_dir
            
            self.log_message(f"开始处理: chunk={chunk}, chunk_num={chunk_num}")
            self.log_message(f"图像文件夹: {img_dir}")
            self.log_message(f"标签文件夹: {coco_label_dir}")
            
            out_img_dir = "./images_new/"
            os.makedirs(out_img_dir, exist_ok=True)
            img_files = [f for f in os.listdir(img_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tif', '.tiff'))]
            img_files.sort()
            
            Len = len(img_files)
            if Len == 0:
                self.log_message("错误: 图像文件夹中没有找到任何图像文件")
                return
                
            chunk_size = Len // chunk_num
            img_files2proc = img_files[chunk*chunk_size: (chunk+1)*chunk_size] if chunk != chunk_num - 1 else img_files[chunk*chunk_size:]
            
            self.log_message(f"图像总数: {Len}, 当前处理: {len(img_files2proc)}张")
            
            prompt = (
                "请基于输入的图像和COCO格式的标签json文件给出以下内容，使用json格式。"
                "第一段详细描述这张图像的内容，主要包括物体、场景、颜色、动作和物体间的相互关系等元素。要求描述细致准确，统计物体数据要精确，重点关注军事情报相关信息；"
                "第二段根据图像内容只生成一个高质量的问答对，这一个问答对针对的是图像中目标的动作意图。使用格式：Q: [问题] \nA: [答案]。问答对应当是信息密度较高的，且答案应当准确而完整。"
                "这两段话封装在如下json结构体内：{'描述': 'xxx', '问答': [{'问题': 'xxx', '回答': 'xxx'}]}"
            )
            
            output_json_path = "./output_sar_show/"
            os.makedirs(output_json_path, exist_ok=True)
            
            for img_file in img_files2proc:
                try:
                    json_path = os.path.splitext(img_file)[0] + ".json"
                    coco_path = os.path.join(coco_label_dir, os.path.basename(json_path))
                    json_out_path = os.path.join(output_json_path, os.path.basename(json_path))
                    
                    if os.path.exists(json_out_path):
                        self.log_message(f"跳过已处理文件: {img_file}")
                        continue
                    
                    coco_text = read_json_as_text(coco_path)
                    prompt_temp = prompt + "\n以下是该张图片的coco格式标注：\n" + (coco_text if coco_text else "")
                    img_path = os.path.join(img_dir, img_file)
                    
                    self.log_message(f"处理中: {img_file}")
                    
                    # 初始化客户端
                    client = OpenAI(
                        base_url="http://localhost:8089/v1",
                        api_key="no-api-key-required"
                    )
                    
                    # 处理图像
                    image_base64 = encode_image_to_base64(img_path)
                    response = client.chat.completions.create(
                        model="InternVL3-8B",
                        messages=[
                            {"role": "system", "content": "你是一个专业的遥感视觉助手，可以分析和回答关于图像的问题。能够全面、详细地描述影像中所有的目标类型、目标数量、目标位置（左上、上部、右上、左部、中部、右部、左下、下部、右下），目标类型包括战车、坦克、汽车、火车、战术小队等陆地目标，航空母舰、巡洋舰、驱逐舰、护卫舰、舰艇、潜艇等海上目标，战斗机、轰炸机、运输机、直升机等空中目标，以及机场、港口、油库、油罐等设施目标，以及图中能够识别到的其他设施及数量，如图中没有出现可不进行描述。输出一段完整的文字描述，包含上述信息，不要生成MarkDown格式。"},
                            {"role": "user", "content": [
                                {"type": "text", "text": prompt_temp},
                                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_base64}"}}
                            ]}
                        ],
                        max_tokens=30000,
                        stream=False
                    )
                    generated_text = response.choices[0].message.content
                    generated_text = remove_markdown(generated_text)
                    
                    parse_and_save_to_json(generated_text, json_out_path)
                    img_out_path = os.path.join(out_img_dir, img_file)
                    shutil.copy(img_path, img_out_path)
                    
                    self.log_message(f"完成: {img_file}")
                except BadRequestError as e:
                    self.log_message(f"处理错误 - 跳过: {img_file} - {str(e)}")
                except Exception as e:
                    self.log_message(f"未知错误 - 跳过: {img_file} - {str(e)}")
            
            self.log_message("数据处理完成!")
        except Exception as e:
            self.log_message(f"启动错误: {str(e)}")

if __name__ == "__main__":
    # 命令行参数解析
    parser = argparse.ArgumentParser(description='数据制备处理工具')
    parser.add_argument('--chunk', type=int, default=0, help='处理块编号')
    parser.add_argument('--chunk_num', type=int, default=5, help='总块数')
    parser.add_argument('--img_dir', type=str, default="./sar_dataset/tif/", help='图像文件夹路径')
    parser.add_argument('--coco_dir', type=str, default="./sar_dataset/json/", help='COCO标签文件夹路径')
    parser.add_argument('--gui', action='store_true', help='使用GUI界面')
    args = parser.parse_args()
    
    if args.gui:
        # GUI模式运行
        app = QApplication(sys.argv)
        window = DataGenerator()
        window.setWindowTitle("数据制备工具")
        window.resize(800, 600)
        window.show()
        sys.exit(app.exec_())
    else:
        # 命令行模式运行
        if args.chunk is None or args.chunk_num is None:
            print("错误: 必须提供 --chunk 和 --chunk_num 参数")
            sys.exit(1)
        
        run_in_command_line(args.chunk, args.chunk_num, args.img_dir, args.coco_dir)
