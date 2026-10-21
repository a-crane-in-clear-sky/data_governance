import os
import json
import io
import re
import base64
import shutil
import sys
import argparse
from tqdm import tqdm
from PIL import Image
from openai import OpenAI, BadRequestError
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
                             QPushButton, QTextEdit, QApplication, QFileDialog)
from PyQt5.QtCore import Qt

# ======================== 工具函数 ========================
def remove_markdown(text):
    """清除文本中的Markdown标记"""
    text = re.sub(r'^#+\s*', '', text, flags=re.MULTILINE)  # 移除标题标记
    text = re.sub(r'[\*\_]{1,2}(.*?)[\*\_]{1,2}', r'\1', text)  # 移除粗体和斜体
    text = re.sub(r'^[\-\*\+]\s*', '', text, flags=re.MULTILINE)  # 移除列表标记
    text = re.sub(r'\n\s*\n', '\n\n', text).strip()  # 压缩多余空行
    return text

def encode_image_to_base64(image_path):
    """将图像编码为Base64字符串"""
    with Image.open(image_path) as img:
        buffered = io.BytesIO()
        img.save(buffered, format=img.format)
        return base64.b64encode(buffered.getvalue()).decode('utf-8')

def parse_and_save_to_json(text, output_file):
    """解析生成的文本并保存为JSON格式"""
    result = {"CAP": "", "Q": "", "A": ""}
    try:
        # 尝试直接解析为JSON
        data = json.loads(text)
        if "描述" in data: result["CAP"] = data["描述"]
        if "问答" in data and data["问答"]:
            if "问题" in data["问答"][0]: result["Q"] = data["问答"][0]["问题"]
            if "回答" in data["问答"][0]: result["A"] = data["问答"][0]["回答"]
    except json.JSONDecodeError:
        # 正则提取关键字段
        cap_match = re.search(r'"描述":\s*"([^"]*)"', text)
        q_match = re.search(r'"问题":\s*"([^"]*)"', text)
        a_match = re.search(r'"回答":\s*"([^"]*)"', text)
        if cap_match: result["CAP"] = cap_match.group(1)
        if q_match: result["Q"] = q_match.group(1)
        if a_match: result["A"] = a_match.group(1)
    
    # 保存结果到文件
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    return result

def read_json_as_text(file_path):
    """读取JSON文件并返回格式化文本"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return json.dumps(json.load(file), ensure_ascii=False, indent=2)
    except Exception:
        return None

# ======================== 核心处理逻辑 ========================
def process_single_image(img_file, img_dir, coco_label_dir, output_json_path, client, log_func):
    """处理单张图像：生成描述、问答对并保存结果"""
    try:
        # 准备文件路径
        json_path = os.path.splitext(img_file)[0] + ".json"
        coco_path = os.path.join(coco_label_dir, json_path)
        json_out_path = os.path.join(output_json_path, json_path)
        img_path = os.path.join(img_dir, img_file)
        
        # 跳过已处理文件
        if os.path.exists(json_out_path):
            log_func(f"跳过已处理文件: {img_file}")
            return
        
        # 读取COCO标签
        coco_text = read_json_as_text(coco_path) or ""
        prompt = (
            "请基于输入的图像和COCO格式的标签json文件给出以下内容，使用json格式。"
            "第一段详细描述这张图像的内容，主要包括物体、场景、颜色、动作和物体间的相互关系等元素。要求描述细致准确，统计物体数据要精确，重点关注军事情报相关信息；"
            "第二段根据图像内容只生成一个高质量的问答对，这一个问答对针对的是图像中目标的动作意图。使用格式：Q: [问题] \nA: [答案]。问答对应当是信息密度较高的，且答案应当准确而完整。"
            "这两段话封装在如下json结构体内：{'描述': 'xxx', '问答': [{'问题': 'xxx', '回答': 'xxx'}]}"
        )
        prompt_temp = f"{prompt}\n以下是该张图片的coco格式标注：\n{coco_text}"
        
        # 处理图像
        log_func(f"处理中: {img_file}")
        image_base64 = encode_image_to_base64(img_path)
        
        # 调用OpenAI模型
        response = client.chat.completions.create(
            model="Qwen2.5-VL-3B",
            messages=[
                {
                    "role": "system",
                    "content": "你是一个专业的遥感视觉助手，可以分析和回答关于图像的问题。能够全面、详细地描述影像中所有的目标类型、目标数量、目标位置（左上、上部、右上、左部、中部、右部、左下、下部、右下），目标类型包括战车、坦克、汽车、火车、战术小队等陆地目标，航空母舰、巡洋舰、驱逐舰、护卫舰、舰艇、潜艇等海上目标，战斗机、轰炸机、运输机、直升机等空中目标，以及机场、港口、油库、油罐等设施目标，以及图中能够识别到的其他设施及数量，如图中没有出现可不进行描述。输出一段完整的文字描述，包含上述信息，不要生成MarkDown格式。"
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt_temp},
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_base64}"}}
                    ]
                }
            ],
            max_tokens=30000,
            stream=False
        )
        
        # 处理模型返回结果
        generated_text = remove_markdown(response.choices[0].message.content)
        parse_and_save_to_json(generated_text, json_out_path)
        log_func(f"完成: {img_file}")
        
    except BadRequestError as e:
        log_func(f"处理错误 - 跳过: {img_file} - {str(e)}")
    except Exception as e:
        log_func(f"未知错误 - 跳过: {img_file} - {str(e)}")

def run_in_command_line(chunk_id, chunk_num, img_dir, coco_label_dir):
    """命令行模式：批量处理图像数据集"""
    print(f"开始处理: chunk_id={chunk_id}, chunk_num={chunk_num}")
    print(f"图像文件夹: {img_dir}")
    print(f"标签文件夹: {coco_label_dir}")
    
    # 初始化OpenAI客户端
    client = OpenAI(base_url="http://10.200.49.51:8102/v1", api_key="no-api-key-required")
    
    # 准备输出目录
    output_json_path = "./output_sar_show/"
    os.makedirs(output_json_path, exist_ok=True)
    
    # 获取待处理图像列表
    img_files = sorted([f for f in os.listdir(img_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tif', '.tiff'))])
    total = len(img_files)
    chunk_size = total // chunk_num
    start_idx = chunk_id * chunk_size
    end_idx = (chunk_id + 1) * chunk_size if chunk_id != chunk_num - 1 else total
    img_files2proc = img_files[start_idx:end_idx]
    
    print(f"图像总数: {total}, 当前处理: {len(img_files2proc)}张")
    
    # 处理每个图像文件
    for img_file in tqdm(img_files2proc):
        process_single_image(
            img_file, 
            img_dir, 
            coco_label_dir, 
            output_json_path, 
            client, 
            print
        )
    
    print("数据处理完成!")

# ======================== GUI界面 ========================
class DataGenerator(QWidget):
    """数据制备工具的GUI界面"""
    def __init__(self):
        super().__init__()
        self.img_dir = "../../../datasets/tif/"
        self.coco_label_dir = "../../../datasets/json/"
        self.setup_ui()
    
    def setup_ui(self):
        """初始化UI组件"""
        layout = QVBoxLayout(self)
        
        # 标题
        title = QLabel("数据制备")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #0066cc; padding: 10px;")
        layout.addWidget(title)
        
        # 文件夹选择
        folder_layout = QVBoxLayout()
        for label, attr, btn_text in [("图像文件夹:", "img_dir", "选择..."), ("标签文件夹:", "coco_label_dir", "选择...")]:
            hbox = QHBoxLayout()
            hbox.addWidget(QLabel(label))
            input_field = QLineEdit(getattr(self, attr))  # rgba(30, 40, 60, 0.8)
            input_field.setStyleSheet("""
                background-color: #ffffff; 
                color: black;
            """)
            input_field.setReadOnly(True)
            hbox.addWidget(input_field, 4)
            
            btn = QPushButton(btn_text)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: rgba(30, 144, 255, 0.5);
                    color: white; border: 1px solid #00ffff;
                    border-radius: 5px; padding: 5px 10px;
                }
                QPushButton:hover { background-color: rgba(30, 144, 255, 0.8); }
            """)
            btn.setMaximumWidth(80)
            btn.clicked.connect(getattr(self, f"select_{attr}"))
            hbox.addWidget(btn, 1)
            folder_layout.addLayout(hbox)
            setattr(self, f"{attr}_input", input_field)
            setattr(self, f"{attr}_btn", btn)
        
        layout.addLayout(folder_layout)
        
        # 参数输入
        params_layout = QVBoxLayout()
        params_layout.addWidget(QLabel("处理参数"))
        # 将chunk重命名为chunk_id
        for label, attr, default in [("Chunk ID:", "chunk_id", "0"), ("Chunk Num:", "chunk_num", "5")]:
            hbox = QHBoxLayout()
            hbox.addWidget(QLabel(label))
            input_field = QLineEdit(default)  # rgba(30, 40, 60, 0.8)
            input_field.setStyleSheet("""
                background-color: #ffffff; 
                color: black;
            """)
            hbox.addWidget(input_field)
            params_layout.addLayout(hbox)
            setattr(self, f"{attr}_input", input_field)
        
        layout.addLayout(params_layout)
        
        # 日志区域
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)  # background-color: rgba(10, 20, 35, 0.8); color: #e0f0ff;
        self.log_output.setStyleSheet("""
            background-color: #ffffff; 
            color: #0066cc; 
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
                color: white; border: 1px solid #00ffff;
                border-radius: 5px; padding: 10px;
                font-size: 16px; font-weight: bold;
            }
            QPushButton:hover { background-color: rgba(30, 144, 255, 0.8); }
        """)
        self.start_btn.clicked.connect(self.start_generation)
        layout.addWidget(self.start_btn)
    
    def select_img_dir(self):
        """选择图像目录"""
        self._select_dir("img_dir", "选择图像文件夹")
    
    def select_coco_label_dir(self):
        """选择标签目录"""
        self._select_dir("coco_label_dir", "选择标签文件夹")
    
    def _select_dir(self, attr, title):
        """通用目录选择方法"""
        folder = QFileDialog.getExistingDirectory(self, title, getattr(self, attr))
        if folder:
            setattr(self, attr, folder)
            getattr(self, f"{attr}_input").setText(folder)
            self.log_message(f"{title}设置为: {folder}")
    
    def log_message(self, message):
        """记录日志消息"""
        self.log_output.append(message)
        QApplication.processEvents()
    
    def start_generation(self):
        """启动数据处理流程"""
        try:
            # 获取参数（将chunk重命名为chunk_id）
            chunk_id = int(self.chunk_id_input.text())
            chunk_num = int(self.chunk_num_input.text())
            img_dir = self.img_dir
            coco_label_dir = self.coco_label_dir
            
            # 准备输出目录
            output_json_path = "./output_sar_show/"
            os.makedirs(output_json_path, exist_ok=True)
            
            # 获取图像文件列表
            img_files = sorted([f for f in os.listdir(img_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tif', '.tiff'))])
            if not img_files:
                self.log_message("错误: 图像文件夹中没有找到任何图像文件")
                return
                
            # 分割处理块
            total = len(img_files)
            chunk_size = total // chunk_num
            start_idx = chunk_id * chunk_size
            end_idx = (chunk_id + 1) * chunk_size if chunk_id != chunk_num - 1 else total
            img_files2proc = img_files[start_idx:end_idx]
            
            self.log_message(f"图像总数: {total}, 当前处理: {len(img_files2proc)}张")
            
            # 初始化OpenAI客户端
            client = OpenAI(base_url="http://10.200.49.51:8102/v1", api_key="no-api-key-required")
            
            # 处理每个图像文件（不再复制图像）
            for img_file in img_files2proc:
                process_single_image(
                    img_file, 
                    img_dir, 
                    coco_label_dir, 
                    output_json_path, 
                    client, 
                    self.log_message
                )
            
            self.log_message("数据处理完成!")
        except Exception as e:
            self.log_message(f"启动错误: {str(e)}")

# ======================== 主程序入口 ========================
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='数据制备处理工具')
    # 将--chunk参数重命名为--chunk_id
    parser.add_argument('--chunk_id', type=int, default=0, help='处理块编号(从0开始)')
    parser.add_argument('--chunk_num', type=int, default=5, help='总块数')
    parser.add_argument('--img_dir', type=str, default="../../../datasets/tif/", help='图像文件夹路径')
    parser.add_argument('--coco_dir', type=str, default="../../../datasets/json/", help='类COCO格式标签文件夹路径')
    parser.add_argument('--gui', action='store_true', help='使用GUI界面')
    args = parser.parse_args()
    
    if args.gui:
        app = QApplication(sys.argv)
        window = DataGenerator()
        window.setWindowTitle("数据制备工具")
        window.resize(800, 600)
        window.show()
        sys.exit(app.exec_())
    else:
        if args.chunk_id is None or args.chunk_num is None:
            print("错误: 必须提供 --chunk_id 和 --chunk_num 参数")
            sys.exit(1)
        run_in_command_line(args.chunk_id, args.chunk_num, args.img_dir, args.coco_dir)
