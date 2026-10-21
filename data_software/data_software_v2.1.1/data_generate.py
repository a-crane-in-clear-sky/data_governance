"""
数据制备工具模块

本模块提供图像数据处理功能，包括：
1. 从图像生成描述和问答对
2. 将结果保存为JSON格式
3. 提供GUI界面和命令行接口

主要功能：
- 图像编码为Base64
- 调用OpenAI模型生成描述和问答
- 解析模型响应并保存结果
- 支持多线程处理
- 提供停止处理功能

作者: Lin, X
日期: 2025-08-05
版本: 2.0.11
"""

import os
import json
import io
import re
import base64
import sys
import argparse
from tqdm import tqdm
from PIL import Image
from openai import OpenAI, BadRequestError
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
                             QPushButton, QTextEdit, QApplication, QFileDialog)
from PyQt5.QtCore import Qt, QThread, pyqtSignal

# ======================== 工具函数 ========================
def remove_markdown(text):
    """
    清除文本中的Markdown标记
    
    参数:
        text (str): 包含Markdown标记的文本
        
    返回:
        str: 清理后的纯文本
    """
    # 移除标题标记 (如 #, ## 等)
    text = re.sub(r'^#+\s*', '', text, flags=re.MULTILINE)
    # 移除粗体和斜体标记 (如 **bold**, *italic*)
    text = re.sub(r'[\*\_]{1,2}(.*?)[\*\_]{1,2}', r'\1', text)
    # 移除列表标记 (如 -, *, +)
    text = re.sub(r'^[\-\*\+]\s*', '', text, flags=re.MULTILINE)
    # 压缩多余空行
    text = re.sub(r'\n\s*\n', '\n\n', text).strip()
    return text

def encode_image_to_base64(image_path):
    """
    将图像编码为Base64字符串
    
    参数:
        image_path (str): 图像文件路径
        
    返回:
        str: Base64编码的图像字符串
    """
    with Image.open(image_path) as img:
        buffered = io.BytesIO()
        img.save(buffered, format=img.format)
        return base64.b64encode(buffered.getvalue()).decode('utf-8')

def parse_and_save_to_json(text, output_file):
    """
    解析生成的文本并保存为JSON格式
    
    参数:
        text (str): 包含描述和问答的文本
        output_file (str): 输出JSON文件路径
        
    返回:
        dict: 解析后的结果字典
    """
    result = {"CAP": "", "Q": "", "A": ""}
    try:
        # 尝试直接解析为JSON
        data = json.loads(text)
        if "描述" in data: result["CAP"] = data["描述"]
        if "问答" in data and data["问答"]:
            if "问题" in data["问答"][0]: result["Q"] = data["问答"][0]["问题"]
            if "回答" in data["问答"][0]: result["A"] = data["问答"][0]["回答"]
    except json.JSONDecodeError:
        # 使用正则表达式提取关键字段
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
    """
    读取JSON文件并返回格式化文本
    
    参数:
        file_path (str): JSON文件路径
        
    返回:
        str: 格式化后的JSON文本，如果文件不存在或解析失败返回None
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return json.dumps(json.load(file), ensure_ascii=False, indent=2)
    except Exception:
        return None

# ======================== 核心处理逻辑 ========================
class ImageProcessor(QThread):
    """
    图像处理线程，用于异步处理图像
    
    属性:
        progress (pyqtSignal): 进度信号，发送处理状态消息
        finished (pyqtSignal): 完成信号，处理结束时发送
    """
    progress = pyqtSignal(str)  # 进度信号
    finished = pyqtSignal()     # 完成信号
    
    def __init__(self, img_files, img_dir, coco_label_dir, output_json_path, model_params, parent=None):
        """
        初始化图像处理线程
        
        参数:
            img_files: 要处理的图像文件列表
            img_dir: 图像目录路径
            coco_label_dir: COCO标签目录路径
            output_json_path: 输出JSON目录路径
            model_params: 模型参数字典 (model_name, max_tokens, temperature, top_p)
            parent: 父对象
        """
        super().__init__(parent)
        self.img_files = img_files
        self.img_dir = img_dir
        self.coco_label_dir = coco_label_dir
        self.output_json_path = output_json_path
        self.model_params = model_params
        self._is_running = True  # 线程运行标志
    
    def run(self):
        """线程主函数，执行图像处理"""
        try:
            # 初始化OpenAI客户端
            client = OpenAI(
                base_url="http://jb-aionlineinferenceservice-9197699405775732736-8090-nhss-job.z2120.nhss.zhejianglab.com:31080/v1",  # "http://10.200.49.51:8102/v1", 
                api_key="EMPTY"
            )
            
            # 处理每个图像文件
            for img_file in self.img_files:
                if not self._is_running:
                    self.progress.emit("处理已停止")
                    break
                
                try:
                    # 准备文件路径
                    json_path = os.path.splitext(img_file)[0] + ".json"
                    coco_path = os.path.join(self.coco_label_dir, json_path)
                    json_out_path = os.path.join(self.output_json_path, json_path)
                    img_path = os.path.join(self.img_dir, img_file)
                    
                    # 跳过已处理文件
                    if os.path.exists(json_out_path):
                        self.progress.emit(f"跳过已处理文件: {img_file}")
                        continue
                    
                    # 读取COCO标签
                    coco_text = read_json_as_text(coco_path) or ""
                    # 使用传入的提示词（修改点）
                    prompt_text = self.model_params.get("prompt_text", "")
                    if not prompt_text:
                        prompt_text = (
                            "请基于输入的图像和COCO格式的标签json文件给出以下内容，使用json格式。"
                            "第一段详细描述这张图像的内容，主要包括物体、场景、颜色、动作和物体间的相互关系等元素。要求描述细致准确，统计物体数据要精确，重点关注军事情报相关信息；"
                            "第二段根据图像内容只生成一个高质量的问答对，这一个问答对针对的是图像中目标的动作意图。使用格式：Q: [问题] \nA: [答案]。问答对应当是信息密度较高的，且答案应当准确而完整。"
                            "这两段话封装在如下json结构体内：{'描述': 'xxx', '问答': [{'问题': 'xxx', '回答': 'xxx'}]}"
                        )
                    
                    # 构造提示文本（使用传入的提示词）
                    prompt_temp = f"{prompt_text}\n以下是该张图片的coco格式标注：\n{coco_text}"
                    
                    # 处理图像
                    self.progress.emit(f"处理中: {img_file}")
                    # 将图像编码为Base64
                    image_base64 = encode_image_to_base64(img_path)
                    
                    # 调用OpenAI模型
                    response = client.chat.completions.create(
                        model=self.model_params["model_name"],
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
                        max_tokens=self.model_params["max_tokens"],
                        temperature=self.model_params["temperature"],
                        top_p=self.model_params["top_p"],
                        stream=False
                    )
                    
                    # 处理模型返回结果
                    generated_text = remove_markdown(response.choices[0].message.content)
                    # 解析并保存为JSON
                    parse_and_save_to_json(generated_text, json_out_path)
                    self.progress.emit(f"完成: {img_file}")
                    
                except BadRequestError as e:
                    # 处理API请求错误
                    self.progress.emit(f"处理错误 - 跳过: {img_file} - {str(e)}")
                except Exception as e:
                    # 处理其他未知错误
                    self.progress.emit(f"未知错误 - 跳过: {img_file} - {str(e)}")
            
            self.progress.emit("数据处理完成!")
        except Exception as e:
            # 处理线程级错误
            self.progress.emit(f"线程错误: {str(e)}")
        finally:
            # 发送完成信号
            self.finished.emit()
    
    def stop(self):
        """停止处理线程"""
        self._is_running = False

# ======================== GUI界面 ========================
class DataGenerator(QWidget):
    """
    数据制备工具的GUI界面
    
    属性:
        img_dir (str): 图像目录路径
        coco_label_dir (str): COCO标签目录路径
        processor (ImageProcessor): 图像处理线程实例
    """
    def __init__(self):
        super().__init__()
        # 默认目录设置
        self.img_dir = "../../../datasets/tif/"
        self.coco_label_dir = "../../../datasets/json/"
        # 默认模型参数
        self.model_name = "Qwen2.5-VL-7B"
        self.max_tokens = 4096
        self.temperature = 0.3
        self.top_p = 0.65
        # 默认提示词
        self.default_prompt = (
            "请基于输入的图像和COCO格式的标签json文件给出以下内容，使用json格式。"
            "第一段详细描述这张图像的内容，主要包括物体、场景、颜色、动作和物体间的相互关系等元素。要求描述细致准确，统计物体数据要精确，重点关注军事情报相关信息；"
            "第二段根据图像内容只生成一个高质量的问答对，这一个问答对针对的是图像中目标的动作意图。使用格式：Q: [问题] \nA: [答案]。问答对应当是信息密度较高的，且答案应当准确而完整。"
            "这两段话封装在如下json结构体内：{'描述': 'xxx', '问答': [{'问题': 'xxx', '回答': 'xxx'}]}"
        )
        # 图像处理线程
        self.processor = None
        # 初始化UI
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
            # 输入字段
            input_field = QLineEdit(getattr(self, attr))
            input_field.setStyleSheet("""
                background-color: #ffffff; 
                color: black;
            """)
            input_field.setReadOnly(True)
            hbox.addWidget(input_field, 4)
            
            # 选择按钮
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
            # 连接按钮点击事件到相应方法
            btn.clicked.connect(getattr(self, f"select_{attr}"))
            hbox.addWidget(btn, 1)
            folder_layout.addLayout(hbox)
            # 保存输入字段和按钮引用
            setattr(self, f"{attr}_input", input_field)
            setattr(self, f"{attr}_btn", btn)
        
        layout.addLayout(folder_layout)
        
        # 参数输入
        params_layout = QVBoxLayout()
        params_layout.addWidget(QLabel("处理参数"))
        # 添加chunk_id和chunk_num输入字段
        for label, attr, default in [("Chunk ID:", "chunk_id", "0"), ("Chunk Num:", "chunk_num", "5")]:
            hbox = QHBoxLayout()
            hbox.addWidget(QLabel(label))
            input_field = QLineEdit(default)
            input_field.setStyleSheet("""
                background-color: #ffffff; 
                color: black;
            """)
            hbox.addWidget(input_field)
            params_layout.addLayout(hbox)
            # 保存输入字段引用
            setattr(self, f"{attr}_input", input_field)
        
        layout.addLayout(params_layout)
        
        # 添加提示词编辑区域（新增部分）
        prompt_layout = QVBoxLayout()
        prompt_layout.addWidget(QLabel("提示词 (可编辑):"))
        self.prompt_edit = QTextEdit(self.default_prompt)
        self.prompt_edit.setStyleSheet("""
            QTextEdit {
                background-color: #ffffff; 
                color: black;
                border: 1px solid #1e90ff;
                font-size: 14px;
            }
        """)
        self.prompt_edit.setMinimumHeight(150)
        prompt_layout.addWidget(self.prompt_edit)
        
        # 添加提示词说明
        prompt_note = QLabel("提示词修改后将用于模型输入，否则使用默认提示词")
        prompt_note.setStyleSheet("color: #888888; font-size: 12px;")
        prompt_layout.addWidget(prompt_note)
        
        layout.addLayout(prompt_layout)
        
        # 日志区域
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setStyleSheet("""
            background-color: #ffffff; 
            color: #0066cc; 
            border: 1px solid #1e90ff;
            font-size: 14px;
        """)
        layout.addWidget(QLabel("处理日志:"))
        layout.addWidget(self.log_output)
        
        # 按钮布局
        button_layout = QHBoxLayout()
        
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
            QPushButton:disabled { background-color: rgba(150, 150, 150, 0.5); }
        """)
        self.start_btn.clicked.connect(self.start_generation)
        button_layout.addWidget(self.start_btn)
        
        # 停止按钮
        self.stop_btn = QPushButton("停止数据制备")
        self.stop_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 69, 0, 0.5);
                color: white; border: 1px solid #ff4500;
                border-radius: 5px; padding: 10px;
                font-size: 16px; font-weight: bold;
            }
            QPushButton:hover { background-color: rgba(255, 69, 0, 0.8); }
            QPushButton:disabled { background-color: rgba(150, 150, 150, 0.5); }
        """)
        self.stop_btn.clicked.connect(self.stop_generation)
        self.stop_btn.setEnabled(False)  # 初始不可用
        button_layout.addWidget(self.stop_btn)
        
        layout.addLayout(button_layout)
    
    def select_img_dir(self):
        """选择图像目录"""
        self._select_dir("img_dir", "选择图像文件夹")
    
    def select_coco_label_dir(self):
        """选择标签目录"""
        self._select_dir("coco_label_dir", "选择标签文件夹")
    
    def _select_dir(self, attr, title):
        """
        通用目录选择方法
        
        参数:
            attr (str): 属性名 (img_dir 或 coco_label_dir)
            title (str): 对话框标题
        """
        folder = QFileDialog.getExistingDirectory(self, title, getattr(self, attr))
        if folder:
            # 更新属性值
            setattr(self, attr, folder)
            # 更新输入字段显示
            getattr(self, f"{attr}_input").setText(folder)
            # 记录日志
            self.log_message(f"{title}设置为: {folder}")
    
    def log_message(self, message):
        """
        记录日志消息
        
        参数:
            message (str): 要记录的日志消息
        """
        self.log_output.append(message)
        # 确保UI及时更新
        QApplication.processEvents()
    
    def start_generation(self):
        """启动数据处理流程"""
        try:
            # 获取参数
            chunk_id = int(self.chunk_id_input.text())
            chunk_num = int(self.chunk_num_input.text())
            img_dir = self.img_dir
            coco_label_dir = self.coco_label_dir
            
            # 获取用户编辑的提示词或使用默认值（新增）
            prompt_text = self.prompt_edit.toPlainText().strip()
            if not prompt_text:
                prompt_text = self.default_prompt
                self.log_message("使用默认提示词")
            else:
                self.log_message("使用自定义提示词")
            
            # 准备输出目录
            output_json_path = "./output_json_dir/"
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
            
            # 准备模型参数
            model_params = {
                "model_name": self.model_name,
                "max_tokens": self.max_tokens,
                "temperature": self.temperature,
                "top_p": self.top_p,
                "prompt_text": prompt_text  # 新增：传递提示词
            }
            
            # 创建并启动处理线程
            self.processor = ImageProcessor(
                img_files2proc, 
                img_dir, 
                coco_label_dir, 
                output_json_path, 
                model_params,
                self
            )
            # 连接信号
            self.processor.progress.connect(self.log_message)
            self.processor.finished.connect(self.on_generation_finished)
            
            # 更新按钮状态
            self.start_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
            
            # 启动线程
            self.processor.start()
            
        except Exception as e:
            self.log_message(f"启动错误: {str(e)}")
    
    def stop_generation(self):
        """停止数据处理流程"""
        if self.processor and self.processor.isRunning():
            self.log_message("正在停止处理...")
            # 请求停止线程
            self.processor.stop()
            # 更新按钮状态
            self.stop_btn.setEnabled(False)
    
    def on_generation_finished(self):
        """处理完成时的回调函数"""
        self.log_message("处理线程已结束")
        # 恢复按钮状态
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        # 清理线程引用
        self.processor = None


# ======================== 命令行模式处理函数 ========================
def run_in_command_line(chunk_id, chunk_num, img_dir, coco_dir):
    """
    命令行模式处理函数
    
    参数:
        chunk_id (int): 处理块编号(从0开始)
        chunk_num (int): 总块数
        img_dir (str): 图像文件夹路径
        coco_dir (str): COCO标签文件夹路径
    """
    # 准备输出目录
    output_json_path = "./output_json_dir/"
    os.makedirs(output_json_path, exist_ok=True)
    
    # 获取图像文件列表
    img_files = sorted([f for f in os.listdir(img_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tif', '.tiff'))])
    if not img_files:
        print("错误: 图像文件夹中没有找到任何图像文件")
        return
        
    # 分割处理块
    total = len(img_files)
    chunk_size = total // chunk_num
    start_idx = chunk_id * chunk_size
    end_idx = (chunk_id + 1) * chunk_size if chunk_id != chunk_num - 1 else total
    img_files2proc = img_files[start_idx:end_idx]
    
    print(f"图像总数: {total}, 当前处理块: {chunk_id}/{chunk_num}")
    print(f"处理图像数量: {len(img_files2proc)}张")
    
    # 模型参数 (使用与GUI相同的默认值)
    model_params = {
        "model_name": "qwen2.5-vl-32B",
        "max_tokens": 4096,
        "temperature": 0.3,
        "top_p": 0.65
    }
    
    # 初始化OpenAI客户端
    client = OpenAI(
        base_url="http://jb-aionlineinferenceservice-9197699405775732736-8090-nhss-job.z2120.nhss.zhejianglab.com:31080/v1",
        api_key="EMPTY"
    )
    
    # 处理进度条
    progress_bar = tqdm(img_files2proc, desc="处理进度", unit="image")
    
    # 处理每个图像文件
    for img_file in progress_bar:
        try:
            # 准备文件路径
            json_path = os.path.splitext(img_file)[0] + ".json"
            coco_path = os.path.join(coco_dir, json_path)
            json_out_path = os.path.join(output_json_path, json_path)
            img_path = os.path.join(img_dir, img_file)
            
            # 跳过已处理文件
            if os.path.exists(json_out_path):
                progress_bar.set_postfix_str(f"跳过: {img_file}")
                continue
            
            # 读取COCO标签
            coco_text = read_json_as_text(coco_path) or ""
            # 构造提示文本
            prompt = (
                "请基于输入的图像和COCO格式的标签json文件给出以下内容，使用json格式。"
                "第一段详细描述这张图像的内容，主要包括物体、场景、颜色、动作和物体间的相互关系等元素。要求描述细致准确，统计物体数据要精确，重点关注军事情报相关信息；"
                "第二段根据图像内容只生成一个高质量的问答对，这一个问答对针对的是图像中目标的动作意图。使用格式：Q: [问题] \nA: [答案]。问答对应当是信息密度较高的，且答案应当准确而完整。"
                "这两段话封装在如下json结构体内：{'描述': 'xxx', '问答': [{'问题': 'xxx', '回答': 'xxx'}]}"
            )
            prompt_temp = f"{prompt}\n以下是该张图片的coco格式标注：\n{coco_text}"
            
            # 将图像编码为Base64
            image_base64 = encode_image_to_base64(img_path)
            
            # 调用OpenAI模型
            response = client.chat.completions.create(
                model=model_params["model_name"],
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
                max_tokens=model_params["max_tokens"],
                temperature=model_params["temperature"],
                top_p=model_params["top_p"],
                stream=False
            )
            
            # 处理模型返回结果
            generated_text = remove_markdown(response.choices[0].message.content)
            # 解析并保存为JSON
            parse_and_save_to_json(generated_text, json_out_path)
            progress_bar.set_postfix_str(f"完成: {img_file}")
            
        except BadRequestError as e:
            # 处理API请求错误
            progress_bar.write(f"处理错误 - 跳过: {img_file} - {str(e)}")
        except Exception as e:
            # 处理其他未知错误
            progress_bar.write(f"未知错误 - 跳过: {img_file} - {str(e)}")
    
    print("数据处理完成!")


# ======================== 主程序入口 ========================
if __name__ == "__main__":
    # 命令行参数解析
    parser = argparse.ArgumentParser(description='数据制备处理工具')
    parser.add_argument('--chunk_id', type=int, default=0, help='处理块编号(从0开始)')
    parser.add_argument('--chunk_num', type=int, default=5, help='总块数')
    parser.add_argument('--img_dir', type=str, default="../../../datasets/tif/", help='图像文件夹路径')
    parser.add_argument('--coco_dir', type=str, default="../../../datasets/json/", help='类COCO格式标签文件夹路径')
    parser.add_argument('--gui', action='store_true', help='使用GUI界面')
    args = parser.parse_args()
    
    if args.gui:
        # GUI模式
        app = QApplication(sys.argv)
        window = DataGenerator()
        window.setWindowTitle("数据制备工具")
        window.resize(800, 600)
        window.show()
        sys.exit(app.exec_())
    else:
        # 命令行模式
        if args.chunk_id is None or args.chunk_num is None:
            print("错误: 必须提供 --chunk_id 和 --chunk_num 参数")
            sys.exit(1)
        # 调用命令行处理函数
        run_in_command_line(args.chunk_id, args.chunk_num, args.img_dir, args.coco_dir)
