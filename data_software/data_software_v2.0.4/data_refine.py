import os
import json
import sys
import threading
import queue
import base64
from PIL import Image, ImageDraw
from openai import OpenAI
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QSplitter, QFileDialog, QMessageBox, QDialog, QVBoxLayout,
    QHBoxLayout, QWidget, QLabel, QTextEdit, QPushButton, QScrollArea, QFrame, QLineEdit,
    QListWidget, QInputDialog, QAction, QMenu, QStatusBar, QToolBar, QSizePolicy, QListWidgetItem,
    QProgressBar, QComboBox, QGroupBox
)
from PyQt5.QtGui import QPixmap, QImage, QKeySequence, QFont, QIcon, QPalette, QColor
from PyQt5.QtCore import Qt, QSize, QThread, pyqtSignal


class ImageTextAnnotator(QMainWindow):     
    def __init__(self):
        super().__init__()
        self.setWindowTitle("多模态（图像-文本）标注查验工具 v2.1")
        self.setGeometry(100, 100, 1200, 800)
        if os.path.exists("CASC-LOGO.png"):
            self.setWindowIcon(QIcon("CASC-LOGO.png"))
        
        # 当前处理状态
        self.image_dir = ""
        self.save_path = ""
        self.json_file_path = ""
        self.current_image_index = 0
        self.image_files = []
        self.annotations = {}
        self.json_data = []
        self.modified = False
        self.annotation_dir = ''
        self.api_key = None
        self.vlm_api_url = "http://localhost:8089/v1"  # VLM API地址
        self.default_prompts = {
            "generate_caption": "请描述这张图像的内容，包括主要对象、场景和重要细节:",
            "generate_vqa": "基于图像内容生成一个视觉问答对，问题应关注图像中的细节:"
        }
        
        # 检测框显示状态
        self.show_bbox = False
        self.current_bboxes = []

        # 断点续查看状态
        self.config_file = "annotator_config.json"
        
        # 创建主界面
        self.create_ui()
        
        # 创建菜单
        self.create_menu()
        
        # 创建工具栏 - 添加了进度条区域
        self.create_toolbar()
        
        # 创建状态队列
        self.api_queue = queue.Queue()
        
        # 创建状态栏
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("就绪")

        # 设置样式
        self.set_style()

        # 然后加载配置
        self.load_config()  # 加载上次的查看进度

        # 创建VLM客户端
        self.vlm_client = OpenAI(
            base_url=self.vlm_api_url,
            api_key="no-api-key-required"
        )    
    
    def load_config(self):
        """加载上次的查看进度配置"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                self.image_dir = config.get("image_dir", "")
                self.annotation_dir = config.get("annotation_dir", "")
                self.json_file_path = config.get("json_file_path", "")
                self.current_image_index = config.get("current_index", 0)
                
                # 尝试加载图像文件列表
                if self.image_dir and os.path.exists(self.image_dir):
                    self.image_files = [f for f in os.listdir(self.image_dir) 
                                       if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tif', '.gif', '.tiff'))]
                    self.image_files.sort()
                    
                    # 初始化进度条
                    self.progress_bar.setMaximum(len(self.image_files))
                    self.progress_bar.setValue(self.current_image_index)
                    self.progress_bar.setVisible(True)
                    self.progress_label.setText(f"{self.current_image_index+1}/{len(self.image_files)}")
                    
                    # 更新路径标签
                    self.update_path_labels()
                    
                    # 加载当前图像
                    self.update_cap_bbox_path()
                    self.load_recent_image()
                
                self.status_bar.showMessage(f"已加载上次进度: {self.current_image_index}/{len(self.image_files)}")
            except Exception as e:
                print(f"加载配置失败: {str(e)}")
    
    def save_config(self):
        """保存当前查看进度到配置文件"""
        config = {
            "image_dir": self.image_dir,
            "annotation_dir": self.annotation_dir,
            "json_file_path": self.json_file_path,
            "current_index": self.current_image_index
        }
        
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存配置失败: {str(e)}")
    
    def set_style(self):
        # 设置应用样式
        self.setStyleSheet("""
            QMainWindow {
                background-color: #0a1423;
            }
            QLabel {
                font-size: 12px;
            }
            QTextEdit {
                background-color: rgba(30, 40, 60, 0.8);
                color: #e0f0ff;
                border: 1px solid #1e90ff;
                border-radius: 4px;
                padding: 5px;
                font-size: 12px;
            }
            QPushButton {
                background-color: #4a86e8;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 5px 10px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #3a76d8;
            }
            QPushButton:pressed {
                background-color: #2a66c8;
            }
            QListWidget {
                background-color: rgba(30, 40, 60, 0.8);
                border: 1px solid #1e90ff;
                border-radius: 4px;
                color: #e0f0ff;
            }
            QScrollArea {
                background-color: rgba(30, 40, 60, 0.8);
                border: 1px solid #1e90ff;
                border-radius: 4px;
            }
            QFrame {
                background-color: rgba(30, 40, 60, 0.8);
                border: 1px solid #1e90ff;
                border-radius: 4px;
            }
            QToolBar {
                background-color: #0a1423;
                border: none;
                padding: 5px;
            }
            QLabel#pathLabel {
                color: #90caf9;
                font-size: 10px;
                background-color: rgba(20, 30, 50, 0.7);
                border: 1px solid #1e90ff;
                border-radius: 3px;
                padding: 3px;
            }
            /* 进度条样式 */
            QProgressBar {
                border: 1px solid #1e90ff;
                border-radius: 4px;
                text-align: center;
                background-color: rgba(20, 30, 50, 0.7);
                color: #e0f0ff;
            }
            QProgressBar::chunk {
                background-color: #4a86e8;
                width: 10px;
            }
        """)
    
    def create_menu(self):
        # 文件菜单
        file_menu = self.menuBar().addMenu("文件")
        
        open_image_action = QAction("选择图像文件夹", self)
        open_image_action.triggered.connect(self.open_image_dir)
        file_menu.addAction(open_image_action)
        
        open_ann_action = QAction("选择标注文件夹", self)
        open_ann_action.triggered.connect(self.open_annotation_dir)
        file_menu.addAction(open_ann_action)
        
        open_json_action = QAction("选择图像描述&视觉问答对json文件", self)
        open_json_action.triggered.connect(self.open_json_file)
        file_menu.addAction(open_json_action)
        
        file_menu.addSeparator()
        
        save_action = QAction("保存标注", self)
        save_action.setShortcut(QKeySequence.Save)
        save_action.triggered.connect(self.save_annotations)
        file_menu.addAction(save_action)
        
        save_as_action = QAction("另存为", self)
        save_as_action.triggered.connect(self.save_annotations_as)
        file_menu.addAction(save_as_action)
        
        file_menu.addSeparator()
        
        # 修改为设置API
        api_action = QAction("设置API", self)
        api_action.triggered.connect(self.set_api_config)
        file_menu.addAction(api_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("退出", self)
        exit_action.setShortcut(QKeySequence.Quit)
        exit_action.triggered.connect(self.confirm_exit)
        file_menu.addAction(exit_action)
        
        # 查看菜单 - 添加上一张和下一张
        view_menu = self.menuBar().addMenu("查看")
        
        prev_action = QAction("上一张", self)
        prev_action.setShortcuts([QKeySequence.MoveToPreviousChar, QKeySequence.MoveToPreviousLine])
        prev_action.triggered.connect(self.prev_image)
        view_menu.addAction(prev_action)
        
        next_action = QAction("下一张", self)
        next_action.setShortcuts([QKeySequence.MoveToNextChar, QKeySequence.MoveToNextLine])
        next_action.triggered.connect(self.next_image)
        view_menu.addAction(next_action)
        
        view_menu.addSeparator()
        
        zoom_in_action = QAction("放大图像", self)
        zoom_in_action.triggered.connect(self.zoom_in)
        view_menu.addAction(zoom_in_action)
        
        zoom_out_action = QAction("缩小图像", self)
        zoom_out_action.triggered.connect(self.zoom_out)
        view_menu.addAction(zoom_out_action)
        
        reset_zoom_action = QAction("实际大小", self)
        reset_zoom_action.triggered.connect(self.reset_zoom)
        view_menu.addAction(reset_zoom_action)
        
        # 帮助菜单
        help_menu = self.menuBar().addMenu("帮助")
        
        help_action = QAction("使用说明", self)
        help_action.triggered.connect(self.show_help)
        help_menu.addAction(help_action)
        
        about_action = QAction("关于", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def create_toolbar(self):
        toolbar = QToolBar("主工具栏")
        toolbar.setIconSize(QSize(24, 24))
        self.addToolBar(Qt.TopToolBarArea, toolbar)
        
        # 上一张按钮 - 添加快捷键
        self.prev_btn = QPushButton("上一张 (←/↑)")
        self.prev_btn.setShortcut(QKeySequence("Left"))
        self.prev_btn.setShortcut(QKeySequence("Up"))
        self.prev_btn.clicked.connect(self.prev_image)
        toolbar.addWidget(self.prev_btn)
        
        # 下一张按钮 - 添加快捷键
        self.next_btn = QPushButton("下一张 (→/↓)")
        self.next_btn.setShortcut(QKeySequence("Right"))
        self.next_btn.setShortcut(QKeySequence("Down"))
        self.next_btn.clicked.connect(self.next_image)
        toolbar.addWidget(self.next_btn)
        toolbar.addSeparator()
        
        # 合并为添加图像描述按钮
        self.add_caption_btn = QPushButton("添加图像描述")
        self.add_caption_btn.clicked.connect(self.show_caption_options)
        toolbar.addWidget(self.add_caption_btn)
        
        self.delete_caption_btn = QPushButton("删除图像描述")
        self.delete_caption_btn.clicked.connect(self.delete_caption)
        toolbar.addWidget(self.delete_caption_btn)
        
        toolbar.addSeparator()
        
        # 合并为添加视觉问答对按钮
        self.add_vqa_btn = QPushButton("添加视觉问答对")
        self.add_vqa_btn.clicked.connect(self.show_vqa_options)
        toolbar.addWidget(self.add_vqa_btn)
        
        self.delete_vqa_btn = QPushButton("删除视觉问答对")
        self.delete_vqa_btn.clicked.connect(self.delete_vqa)
        toolbar.addWidget(self.delete_vqa_btn)
        
        toolbar.addSeparator()
        
        # 检测框显示按钮
        self.show_bbox_btn = QPushButton("显示检测框")
        self.show_bbox_btn.clicked.connect(self.toggle_show_bbox)
        toolbar.addWidget(self.show_bbox_btn)
        
        self.hide_bbox_btn = QPushButton("不显示检测框")
        self.hide_bbox_btn.clicked.connect(self.toggle_hide_bbox)
        toolbar.addWidget(self.hide_bbox_btn)
        
        toolbar.addSeparator()
        
        # 保存按钮 - 修改功能
        self.save_btn = QPushButton("保存 (Ctrl+S)")
        self.save_btn.setShortcut(QKeySequence.Save)
        self.save_btn.clicked.connect(self.save_annotations)
        toolbar.addWidget(self.save_btn)
        
        # 进度条区域 - 添加到这里
        progress_layout = QHBoxLayout()
        progress_widget = QWidget()
        progress_widget.setLayout(progress_layout)
        
        # 进度标签
        self.progress_label = QLabel("0/0")
        self.progress_label.setAlignment(Qt.AlignCenter)
        self.progress_label.setMinimumWidth(80)
        progress_layout.addWidget(self.progress_label)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setAlignment(Qt.AlignCenter)
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat("0/0")
        progress_layout.addWidget(self.progress_bar)

        # 设置进度条显示百分比
        self.progress_bar.setFormat("%p%")  # ("%p% (%v/%m)")
        self.progress_bar.setAlignment(Qt.AlignCenter)
        
        # 将进度条区域添加到工具栏
        toolbar.addWidget(progress_widget)
        
        # 断点续查按钮
        self.restore_btn = QPushButton("断点续查")
        self.restore_btn.clicked.connect(self.restore_last_position)
        toolbar.addWidget(self.restore_btn)
    
    def open_json_file(self):
        """打开JSON文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "选择图像描述&视觉问答对json文件", 
            "", 
            "JSON文件 (*.json);;所有文件 (*)"
        )
        
        if not file_path:
            return
            
        self.json_file_path = file_path
        self.load_json_data()
        self.update_path_labels()
        self.status_bar.showMessage(f"JSON文件已加载: {os.path.abspath(self.json_file_path)}")
        
        # 保存配置
        self.save_config()
    
    def load_json_data(self):
        """加载JSON数据"""
        if not self.json_file_path or not os.path.exists(self.json_file_path):
            return
            
        try:
            with open(self.json_file_path, 'r', encoding='utf-8') as f:
                self.json_data = json.load(f)
            self.status_bar.showMessage(f"JSON文件加载成功，共 {len(self.json_data)} 条记录")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"无法加载JSON文件: {str(e)}")
            self.json_data = []
    
    def get_image_data(self, image_name):
        """根据图像名称获取JSON中的对应数据"""
        if not self.json_data:
            return None
            
        base_name = os.path.splitext(image_name)[0]
        
        # 尝试通过id匹配
        for item in self.json_data:
            if item.get("id") == base_name:
                return item
        
        # 尝试通过image路径匹配
        for item in self.json_data:
            image_path = item.get("image", "")
            if os.path.basename(image_path) == image_name:
                return item
                
        return None
    
    def get_caption_from_json(self, image_data):
        """从JSON数据中提取图像描述"""
        if not image_data:
            return ""
            
        conversations = image_data.get("conversations", [])
        if not conversations:
            return ""
            
        # 找到第一个gpt消息作为图像描述
        for conv in conversations:
            if conv.get("from") == "gpt":
                return conv.get("value", "")
                
        return ""
    
    def get_vqa_from_json(self, image_data):
        """从JSON数据中提取视觉问答对"""
        if not image_data:
            return []
            
        conversations = image_data.get("conversations", [])
        if not conversations:
            return []
            
        qa_pairs = []
        current_question = ""
        
        # 跳过第一个gpt消息（图像描述）
        start_index = 0
        for i, conv in enumerate(conversations):
            if conv.get("from") == "gpt":
                start_index = i + 1
                break
                
        # 提取问答对（human后面跟着gpt）
        for i in range(start_index, len(conversations)):
            conv = conversations[i]
            if conv.get("from") == "human":
                current_question = conv.get("value", "")
            elif conv.get("from") == "gpt" and current_question:
                answer = conv.get("value", "")
                qa_pairs.append({
                    "question": current_question,
                    "answer": answer
                })
                current_question = ""
                
        return qa_pairs
    
    def restore_last_position(self):
        """恢复上次查看的位置"""
        if self.image_files:
            # 加载上次保存的配置
            self.load_config()
            
            # 显示进度
            self.status_bar.showMessage(f"已恢复上次查看位置: {self.current_image_index+1}/{len(self.image_files)}")
        else:
            QMessageBox.information(self, "提示", "请先选择图像文件夹")
    
    def toggle_show_bbox(self):
        """切换显示检测框"""
        # 检查是否加载了图像
        if not self.image_files or self.current_image_index >= len(self.image_files):
            QMessageBox.information(self, "提示", "请先选择图像文件夹和标注文件夹")
            return
        
        # 检查是否设置了标注文件夹
        if not self.annotation_dir:
            QMessageBox.information(self, "提示", "请先选择标注文件夹")
            return
        
        self.show_bbox = True
        self.load_current_bboxes()
        self.display_image(self.current_image)
    
    def toggle_hide_bbox(self):
        """切换隐藏检测框"""
        # 检查是否加载了图像
        if not self.image_files or self.current_image_index >= len(self.image_files):
            QMessageBox.information(self, "提示", "请先选择图像文件夹和标注文件夹")
            return
        
        # 检查是否设置了标注文件夹
        if not self.annotation_dir:
            QMessageBox.information(self, "提示", "请先选择标注文件夹")
            return
        
        self.show_bbox = False
        self.display_image(self.current_image)
    
    def load_current_bboxes(self):
        """加载当前图像的检测框"""
        if not self.image_files or self.current_image_index >= len(self.image_files):
            return
        
        # 获取当前图像对应的标注文件路径
        img_name = self.image_files[self.current_image_index]
        base_name = os.path.splitext(img_name)[0]
        annotation_path = os.path.join(self.annotation_dir, f"{base_name}.json")
        
        if not os.path.exists(annotation_path):
            self.current_bboxes = []
            return
        
        try:
            with open(annotation_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.current_bboxes = data.get("annotations", [])
        except Exception as e:
            self.current_bboxes = []
            self.status_bar.showMessage(f"加载检测框失败: {str(e)}")
    
    def create_ui(self):
        # 创建主分割器
        main_splitter = QSplitter(Qt.Horizontal)
        self.setCentralWidget(main_splitter)
        
        # 左侧图像面板
        self.image_frame = QWidget()
        image_layout = QVBoxLayout(self.image_frame)
        self.image_frame.setLayout(image_layout)
        
        # 图像显示区域
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setMinimumSize(400, 400)
        
        # 滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidget(self.image_label)
        scroll_area.setWidgetResizable(True)
        image_layout.addWidget(scroll_area)
        
        # 图像路径标签
        self.image_path_label = QLabel("图像路径: 尚未加载")
        self.image_path_label.setObjectName("pathLabel")
        image_layout.addWidget(self.image_path_label)
        
        # 右侧文本面板
        self.text_frame = QWidget()
        text_layout = QVBoxLayout(self.text_frame)
        self.text_frame.setLayout(text_layout)
        
        # 描述区域
        desc_group = QGroupBox("图像描述")
        desc_group.setStyleSheet("""
            QGroupBox {
                background-color: rgba(30, 40, 60, 0.8);
                color: #00ffff;
                border: 1px solid #00ffff;
                border-radius: 5px;
                margin-top: 1ex;
                font-size: 14px;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: 0 5px;
            }
        """)
        desc_layout = QVBoxLayout(desc_group)
        
        self.desc_text = QTextEdit()
        self.desc_text.setMinimumHeight(100)
        self.desc_text.textChanged.connect(self.on_text_change)
        
        # 解决输入法问题：禁用输入法
        self.desc_text.setInputMethodHints(Qt.ImhNone)
        
        desc_layout.addWidget(self.desc_text, 1)
        
        # 描述来源标签
        self.desc_source_label = QLabel("描述来源: 尚未加载")
        self.desc_source_label.setObjectName("pathLabel")
        desc_layout.addWidget(self.desc_source_label)
        
        text_layout.addWidget(desc_group)
        
        # 问答区域
        qa_group = QGroupBox("图文问答")
        qa_group.setStyleSheet("""
            QGroupBox {
                background-color: rgba(30, 40, 60, 0.8);
                color: #00ffff;
                border: 1px solid #00ffff;
                border-radius: 5px;
                margin-top: 1ex;
                font-size: 14px;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: 0 5px;
            }
        """)
        qa_layout = QVBoxLayout(qa_group)
        
        # 问答列表
        self.qa_scroll = QScrollArea()
        self.qa_scroll.setWidgetResizable(True)
        self.qa_container = QWidget()
        self.qa_container_layout = QVBoxLayout(self.qa_container)
        self.qa_container_layout.setAlignment(Qt.AlignTop)
        self.qa_container.setLayout(self.qa_container_layout)
        self.qa_scroll.setWidget(self.qa_container)
        
        qa_layout.addWidget(self.qa_scroll)
        
        # 问答来源标签
        self.qa_source_label = QLabel("问答来源: 尚未加载")
        self.qa_source_label.setObjectName("pathLabel")
        qa_layout.addWidget(self.qa_source_label)
        
        text_layout.addWidget(qa_group, 3)
        
        # 保存路径标签
        self.save_path_label = QLabel("保存路径: 尚未设置")
        self.save_path_label.setObjectName("pathLabel")
        text_layout.addWidget(self.save_path_label)
        
        # 将左右面板添加到分割器
        main_splitter.addWidget(self.image_frame)
        main_splitter.addWidget(self.text_frame)
        
        # 设置分割器比例
        main_splitter.setSizes([800, 400])
    
    def on_text_change(self):
        self.modified = True
    
    def set_api_config(self):
        """设置API配置"""
        dialog = QDialog(self)
        dialog.setWindowTitle("设置API")
        dialog.setGeometry(300, 300, 400, 200)
        
        layout = QVBoxLayout(dialog)
        
        # API地址
        api_url_label = QLabel("API地址:")
        layout.addWidget(api_url_label)
        
        self.api_url_edit = QLineEdit(self.vlm_api_url)
        # 解决输入法问题：禁用输入法
        self.api_url_edit.setInputMethodHints(Qt.ImhNone)
        layout.addWidget(self.api_url_edit)
        
        # API密钥
        api_key_label = QLabel("API密钥 (本地调用请使用: no-api-key-required):")
        layout.addWidget(api_key_label)
        
        self.api_key_edit = QLineEdit(self.api_key if self.api_key else "")
        # 解决输入法问题：禁用输入法
        self.api_key_edit.setInputMethodHints(Qt.ImhNone)
        layout.addWidget(self.api_key_edit)
        
        # 按钮布局
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("保存")
        save_btn.clicked.connect(lambda: self.save_api_config(dialog))
        btn_layout.addWidget(save_btn)
        
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(dialog.reject)
        btn_layout.addWidget(cancel_btn)
        
        layout.addLayout(btn_layout)
        dialog.exec_()
    
    def save_api_config(self, dialog):
        """保存API配置"""
        self.vlm_api_url = self.api_url_edit.text()
        self.api_key = self.api_key_edit.text()
        
        # 更新VLM客户端
        self.vlm_client = OpenAI(
            base_url=self.vlm_api_url,
            api_key=self.api_key if self.api_key else "no-api-key-required"
        )
        
        dialog.accept()
        QMessageBox.information(self, "成功", "API配置已更新")
    
    def update_cap_bbox_path(self):
        """实时更新标注信息路径"""
        if self.image_files and self.current_image_index < len(self.image_files):
            path_file_temp, _ = os.path.splitext(self.image_files[self.current_image_index])
            path_file_temp = path_file_temp + '.json'
            self.annotation_path = os.path.join(self.annotation_dir, path_file_temp)
    
    def update_path_labels(self):
        """更新所有路径标签"""
        # 图像路径
        if self.image_files and self.current_image_index < len(self.image_files):
            image_path = os.path.join(self.image_dir, self.image_files[self.current_image_index])
            self.image_path_label.setText(f"图像路径: {os.path.abspath(image_path)}")
        
        # 描述来源
        if self.json_file_path:
            self.desc_source_label.setText(f"描述来源: {os.path.abspath(self.json_file_path)}")
        else:
            self.desc_source_label.setText("描述来源: 尚未加载")
        
        # 问答来源
        if self.json_file_path:
            self.qa_source_label.setText(f"问答来源: {os.path.abspath(self.json_file_path)}")
        else:
            self.qa_source_label.setText("问答来源: 尚未加载")
        
        # 保存路径
        if self.save_path:
            self.save_path_label.setText(f"保存路径: {os.path.abspath(self.save_path)}")
        else:
            self.save_path_label.setText("保存路径: 尚未设置")

    def load_recent_image(self):
        """加载当前选中的图像"""
        if not self.image_files:
            return
        
        # 更新进度条
        self.progress_bar.setValue(self.current_image_index)
        self.progress_label.setText(f"{self.current_image_index+1}/{len(self.image_files)}")
        
        image_path = os.path.join(self.image_dir, self.image_files[self.current_image_index])
        self.status_bar.showMessage(f"加载图像: {self.image_files[self.current_image_index]}")
        
        # 更新图像路径标签
        self.image_path_label.setText(f"图像路径: {os.path.abspath(image_path)}")
        
        # 在新线程中加载图像
        self.image_loader = ImageLoader(image_path)
        self.image_loader.image_loaded.connect(self.display_image)
        self.image_loader.start()
        
        # 加载JSON中的描述和问答对
        self.load_json_content()

    def load_json_content(self):
        """从JSON文件中加载描述和问答对"""
        if not self.json_file_path or not os.path.exists(self.json_file_path):
            return
            
        # 获取当前图像对应的JSON数据
        image_data = self.get_image_data(self.image_files[self.current_image_index])
        
        if image_data:
            # 加载图像描述
            caption = self.get_caption_from_json(image_data)
            self.desc_text.setPlainText(caption)
            
            # 加载视觉问答对
            self.clear_qa_rows()
            qa_pairs = self.get_vqa_from_json(image_data)
            for pair in qa_pairs:
                self.add_qa_row(pair["question"], pair["answer"])
            
            self.status_bar.showMessage(f"已从JSON加载描述和问答对")
        else:
            # 清空描述和问答对
            self.desc_text.clear()
            self.clear_qa_rows()
            self.status_bar.showMessage("当前图像在JSON中无对应数据")
    
    def display_image(self, image):
        """显示当前图像"""
        if image is None:
            return
        
        self.current_image = image
        original_width, original_height = image.size
        
        # 调整图像大小以适应显示区域
        max_size = self.image_label.size()
        label_width = max_size.width()
        label_height = max_size.height()
        
        # 计算缩放比例
        width_ratio = label_width / original_width
        height_ratio = label_height / original_height
        ratio = min(width_ratio, height_ratio)
        
        # 创建显示用的图像副本
        display_image = image.copy()
        
        # 如果需要显示检测框
        if self.show_bbox and self.current_bboxes:
            try:
                draw = ImageDraw.Draw(display_image)
                
                # 绘制所有检测框
                for annotation in self.current_bboxes:
                    # 获取坐标点
                    coordinates = annotation.get("coordinates of the corner point(Col,Row)", [])
                    if len(coordinates) == 4:  # 需要4个角点
                        # 解析坐标字符串
                        points = []
                        for coord_str in coordinates:
                            col, row = map(int, coord_str.split(','))
                            points.append((col, row))
                        
                        # 确保坐标在图像范围内
                        points = [
                            (max(0, min(p[0], original_width - 1)), 
                            max(0, min(p[1], original_height - 1)))
                            for p in points
                        ]
                        
                        # 绘制多边形
                        draw.polygon(points, outline="red", width=2)
                        
                        # 添加类别标签
                        class_name = annotation.get("class", "")
                        label = annotation.get("label", "")
                        if class_name or label:
                            text = f"{class_name}-{label}" if label else class_name
                            draw.text(points[0], text, fill="red")
                    
                    print(f"成功绘制 {len(self.current_bboxes)} 个检测框")
            except Exception as e:
                print(f"绘制检测框失败: {str(e)}")
                self.status_bar.showMessage(f"绘制检测框失败: {str(e)}")
        
        # 调整图像大小以适应显示区域
        if ratio < 1:  # 只在需要时缩小
            new_size = (int(original_width * ratio), int(original_height * ratio))
            display_image = display_image.resize(new_size, Image.LANCZOS)
        
        # 转换为QPixmap
        if display_image.mode == 'RGBA':
            qimage = QImage(display_image.tobytes(), display_image.width, display_image.height, 
                            display_image.width * 4, QImage.Format_RGBA8888)
        else:
            # 转换为RGB以确保兼容性
            rgb_image = display_image.convert('RGB')
            qimage = QImage(rgb_image.tobytes(), rgb_image.width, rgb_image.height, 
                            rgb_image.width * 3, QImage.Format_RGB888)
        
        pixmap = QPixmap.fromImage(qimage)
        
        # 更新图像标签
        self.image_label.setPixmap(pixmap)
        
        # 更新状态
        img_name = self.image_files[self.current_image_index]
        self.status_bar.showMessage(f"图像加载完成: {img_name}")
    
    def show_caption_options(self):
        """显示图像描述选项"""
        dialog = QDialog(self)
        dialog.setWindowTitle("添加图像描述")
        dialog.setMinimumSize(300, 200)
        
        layout = QVBoxLayout(dialog)
        
        # 选项按钮
        blank_btn = QPushButton("添加空白的图像描述")
        blank_btn.clicked.connect(lambda: self.add_blank_caption(dialog))
        layout.addWidget(blank_btn)
        
        load_btn = QPushButton("读取已有的图像描述")
        load_btn.clicked.connect(lambda: self.load_existing_caption(dialog))
        layout.addWidget(load_btn)
        
        generate_btn = QPushButton("VLM生成图像描述")
        generate_btn.clicked.connect(lambda: self.generate_caption_with_vlm(dialog))
        layout.addWidget(generate_btn)
        
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(dialog.reject)
        layout.addWidget(cancel_btn)
        
        dialog.exec_()
    
    def show_vqa_options(self):
        """显示视觉问答选项"""
        dialog = QDialog(self)
        dialog.setWindowTitle("添加视觉问答对")
        dialog.setMinimumSize(300, 200)
        
        layout = QVBoxLayout(dialog)
        
        # 选项按钮
        blank_btn = QPushButton("添加空白的视觉问答对")
        blank_btn.clicked.connect(lambda: self.add_blank_vqa(dialog))
        layout.addWidget(blank_btn)
        
        load_btn = QPushButton("读取已有的视觉问答对")
        load_btn.clicked.connect(lambda: self.load_existing_vqa(dialog))
        layout.addWidget(load_btn)
        
        generate_btn = QPushButton("VLM生成视觉问答对")
        generate_btn.clicked.connect(lambda: self.generate_vqa_with_vlm(dialog))
        layout.addWidget(generate_btn)
        
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(dialog.reject)
        layout.addWidget(cancel_btn)
        
        dialog.exec_()
    
    def add_blank_caption(self, dialog):
        """添加空白描述"""
        dialog.close()
        self.desc_text.clear()
        self.modified = True
        self.desc_source_label.setText("描述来源: 用户手动添加")
        self.status_bar.showMessage("已添加空白描述")
    
    def add_blank_vqa(self, dialog):
        """添加空白问答对"""
        dialog.close()
        self.add_qa_row()
        self.modified = True
        self.qa_source_label.setText("问答来源: 用户手动添加")
        self.status_bar.showMessage("已添加空白问答对")
    
    def load_existing_caption(self, dialog=None):
        """加载已有的图像描述"""
        if not self.json_file_path:
            QMessageBox.warning(self, "警告", "请先加载JSON文件")
            if dialog:
                dialog.close()
            return
        
        # 获取当前图像对应的JSON数据
        image_data = self.get_image_data(self.image_files[self.current_image_index])
        
        if not image_data:
            QMessageBox.warning(self, "警告", "当前图像在JSON中无对应数据")
            if dialog:
                dialog.close()
            return
        
        caption = self.get_caption_from_json(image_data)
        self.desc_text.setPlainText(caption)
        self.modified = True
        self.desc_source_label.setText(f"描述来源: {os.path.abspath(self.json_file_path)}")
        self.status_bar.showMessage("已加载已有的图像描述")
        
        if dialog:
            dialog.close()
    
    def generate_caption_with_vlm(self, dialog=None):
        """使用VLM生成图像描述"""
        if not hasattr(self, 'current_image'):
            QMessageBox.warning(self, "警告", "请先加载图像")
            if dialog:
                dialog.close()
            return
        
        # 弹出提示词对话框
        prompt_dialog = QDialog(self)
        prompt_dialog.setWindowTitle("图像描述生成设置")
        prompt_dialog.setMinimumSize(400, 300)
        
        layout = QVBoxLayout(prompt_dialog)
        
        # 提示词编辑
        prompt_label = QLabel("提示词:")
        layout.addWidget(prompt_label)
        
        prompt_edit = QTextEdit()
        prompt_edit.setPlainText(self.default_prompts["generate_caption"])
        prompt_edit.setMinimumHeight(100)
        
        # 解决输入法问题：禁用输入法
        prompt_edit.setInputMethodHints(Qt.ImhNone)
        
        layout.addWidget(prompt_edit)
        
        # 处理按钮
        btn_layout = QHBoxLayout()
        generate_btn = QPushButton("生成")
        generate_btn.clicked.connect(lambda: self.process_caption_generation(prompt_dialog, prompt_edit.toPlainText()))
        btn_layout.addWidget(generate_btn)
        
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(prompt_dialog.reject)
        btn_layout.addWidget(cancel_btn)
        
        layout.addLayout(btn_layout)
        prompt_dialog.exec_()
        
        if dialog:
            dialog.close()
    
    def process_caption_generation(self, dialog, prompt):
        """处理图像描述生成"""
        dialog.close()
        
        # 显示处理中状态
        self.status_bar.showMessage("正在调用VLM生成图像描述...")
        QApplication.processEvents()
        
        try:
            # 调用VLM API生成描述
            caption = self.call_vlm_api(prompt, "caption")
            self.desc_text.setPlainText(caption)
            self.modified = True
            self.desc_source_label.setText("描述来源: VLM生成")
            self.status_bar.showMessage("图像描述生成完成")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"生成图像描述失败: {str(e)}")
            self.status_bar.showMessage("生成失败")
    
    def delete_caption(self):
        """删除当前图像描述"""
        self.desc_text.clear()
        self.modified = True
        self.desc_source_label.setText("描述来源: 已删除")
        self.status_bar.showMessage("已删除图像描述")
    
    def load_existing_vqa(self, dialog=None):
        """加载已有的视觉问答对"""
        if not self.json_file_path:
            QMessageBox.warning(self, "警告", "请先加载JSON文件")
            if dialog:
                dialog.close()
            return
        
        # 获取当前图像对应的JSON数据
        image_data = self.get_image_data(self.image_files[self.current_image_index])
        
        if not image_data:
            QMessageBox.warning(self, "警告", "当前图像在JSON中无对应数据")
            if dialog:
                dialog.close()
            return
        
        # 清空之前的QA对
        self.clear_qa_rows()
        
        # 加载视觉问答对
        qa_pairs = self.get_vqa_from_json(image_data)
        for pair in qa_pairs:
            self.add_qa_row(pair["question"], pair["answer"])
        
        self.modified = True
        self.qa_source_label.setText(f"问答来源: {os.path.abspath(self.json_file_path)}")
        self.status_bar.showMessage("已加载已有的视觉问答对")
        
        if dialog:
            dialog.close()
    
    def generate_vqa_with_vlm(self, dialog=None):
        """使用VLM生成视觉问答对"""
        if not hasattr(self, 'current_image'):
            QMessageBox.warning(self, "警告", "请先加载图像")
            if dialog:
                dialog.close()
            return
        
        # 弹出提示词对话框
        prompt_dialog = QDialog(self)
        prompt_dialog.setWindowTitle("视觉问答对生成设置")
        prompt_dialog.setMinimumSize(400, 300)
        
        layout = QVBoxLayout(prompt_dialog)
        
        # 提示词编辑
        prompt_label = QLabel("提示词:")
        layout.addWidget(prompt_label)
        
        prompt_edit = QTextEdit()
        prompt_edit.setPlainText(self.default_prompts["generate_vqa"])
        prompt_edit.setMinimumHeight(100)
        
        # 解决输入法问题：禁用输入法
        prompt_edit.setInputMethodHints(Qt.ImhNone)
        
        layout.addWidget(prompt_edit)
        
        # 处理按钮
        btn_layout = QHBoxLayout()
        generate_btn = QPushButton("生成")
        generate_btn.clicked.connect(lambda: self.process_vqa_generation(prompt_dialog, prompt_edit.toPlainText()))
        btn_layout.addWidget(generate_btn)
        
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(prompt_dialog.reject)
        btn_layout.addWidget(cancel_btn)
        
        layout.addLayout(btn_layout)
        prompt_dialog.exec_()
        
        if dialog:
            dialog.close()
    
    def process_vqa_generation(self, dialog, prompt):
        """处理视觉问答对生成"""
        dialog.close()
        
        # 显示处理中状态
        self.status_bar.showMessage("正在调用VLM生成视觉问答对...")
        QApplication.processEvents()
        
        try:
            # 调用VLM API生成问答对
            vqa_result = self.call_vlm_api(prompt, "vqa")
            
            # 尝试解析问答对
            if "问题:" in vqa_result and "答案:" in vqa_result:
                # 提取问题和答案
                parts = vqa_result.split("答案:")
                question = parts[0].replace("问题:", "").strip()
                answer = parts[1].strip()
                self.add_qa_row(question, answer)
            else:
                # 无法解析，直接显示全部内容
                self.add_qa_row("VLM生成的问题", vqa_result)
            
            self.modified = True
            self.qa_source_label.setText("问答来源: VLM生成")
            self.status_bar.showMessage("视觉问答对生成完成")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"生成视觉问答对失败: {str(e)}")
            self.status_bar.showMessage("生成失败")
    
    def delete_vqa(self):
        """删除所有视觉问答对"""
        self.clear_qa_rows()
        self.modified = True
        self.qa_source_label.setText("问答来源: 已删除")
        self.status_bar.showMessage("已删除所有视觉问答对")
    
    def encode_image_to_base64(self, image_path):
        """将图像编码为base64字符串"""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    
    def call_vlm_api(self, prompt, task_type):
        """调用VLM API生成内容"""
        if not hasattr(self, 'current_image') or not self.image_files:
            raise Exception("没有加载图像")
        
        # 获取当前图像路径
        image_path = os.path.join(self.image_dir, self.image_files[self.current_image_index])
        
        # 将图像编码为base64
        image_base64 = self.encode_image_to_base64(image_path)
        
        # 根据任务类型设置系统提示
        if task_type == "caption":
            system_prompt = ("你是一个专业的遥感视觉助手，可以分析和回答关于图像的问题。能够全面、详细地描述影像中所有的目标类型、目标数量、目标位置（左上、上部、右上、左部、中部、右部、左下、下部、右下），目标类型包括战车、坦克、汽车、火车、战术小队等陆地目标，航空母舰、巡洋舰、驱逐舰、护卫舰、舰艇、潜艇等海上目标，战斗机、轰炸机、运输机、直升机等空中目标，以及机场、港口、油库、油罐等设施目标，以及图中能够识别到的其他设施及数量，如图中没有出现可不进行描述。输出一段完整的文字描述，包含上述信息，不要生成MarkDown格式。")
        else:  # vqa任务
            system_prompt = "你是一个专业的遥感视觉助手，可以分析和回答关于图像的问题。"
        
        try:
            # 调用VLM API
            response = self.vlm_client.chat.completions.create(
                model="InternVL3-8B",
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    {
                        "role": "user",
                        "content": [
                            {    
                                "type": "text", 
                                "text": prompt
                            },
                            { 
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{image_base64}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=30000,
                stream=False
            )
            return response.choices[0].message.content
        except Exception as e:
            raise Exception(f"VLM API调用失败: {str(e)}")
    
    def clear_qa_rows(self):
        """清空所有问答对"""
        while self.qa_container_layout.count():
            item = self.qa_container_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
    
    def add_qa_row(self, question="", answer="", idx=None):
        """添加一个问答对行"""
        if idx is None:
            idx = self.qa_container_layout.count()
        
        qa_frame = QFrame()
        qa_frame.setFrameShape(QFrame.StyledPanel)
        qa_layout = QVBoxLayout(qa_frame)
        
        # 问题标签
        q_label = QLabel("问题:")
        qa_layout.addWidget(q_label)
        
        # 问题文本框
        question_txt = QTextEdit()
        question_txt.setPlainText(question)
        question_txt.setMinimumHeight(50)
        question_txt.textChanged.connect(self.on_text_change)
        
        # 解决输入法问题：禁用输入法
        question_txt.setInputMethodHints(Qt.ImhNone)
        
        qa_layout.addWidget(question_txt)
        
        # 答案标签
        a_label = QLabel("答案:")
        qa_layout.addWidget(a_label)
        
        # 答案文本框
        answer_txt = QTextEdit()
        answer_txt.setPlainText(answer)
        answer_txt.setMinimumHeight(80)
        answer_txt.textChanged.connect(self.on_text_change)
        
        # 解决输入法问题：禁用输入法
        answer_txt.setInputMethodHints(Qt.ImhNone)
        
        qa_layout.addWidget(answer_txt)
        
        # 删除按钮
        btn_delete = QPushButton("删除")
        btn_delete.clicked.connect(lambda: self.delete_qa_row(qa_frame))
        qa_layout.addWidget(btn_delete)
        
        # 存储文本框引用
        qa_frame.question_text = question_txt
        qa_frame.answer_text = answer_txt
        
        # 添加到容器
        self.qa_container_layout.addWidget(qa_frame)
    
    def delete_qa_row(self, frame):
        """删除特定的问答对行"""
        frame.deleteLater()
        self.modified = True
    
    def prev_image(self):
        """显示上一张图像"""
        if not self.image_files or self.current_image_index <= 0:
            return
        
        self.save_current_annotation()
        self.current_image_index -= 1
        self.update_cap_bbox_path()
        self.load_current_bboxes()
        self.load_recent_image()
        
        # 保存当前查看位置
        self.save_config()
    
    def next_image(self):
        """显示下一张图像"""
        if not self.image_files or self.current_image_index >= len(self.image_files) - 1:
            return
        
        self.save_current_annotation()
        self.current_image_index += 1
        self.update_cap_bbox_path()
        self.load_current_bboxes()
        self.load_recent_image()
        
        # 保存当前查看位置
        self.save_config()

    def open_image_dir(self):
        """打开图像文件夹"""
        dir_path = QFileDialog.getExistingDirectory(self, "选择图像文件夹")
        if not dir_path:
            return
        
        self.image_dir = dir_path
        self.image_files = [f for f in os.listdir(dir_path) 
                           if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tif', '.gif', '.tiff'))]
        self.image_files.sort()
        
        if not self.image_files:
            QMessageBox.critical(self, "错误", "选择的文件夹中没有图像文件")
            return
        
        # 初始化进度条
        self.progress_bar.setMaximum(len(self.image_files))
        self.progress_bar.setValue(self.current_image_index)
        self.progress_bar.setVisible(True)
        self.progress_label.setText(f"{self.current_image_index+1}/{len(self.image_files)}")
        
        self.current_image_index = 0
        self.update_cap_bbox_path()
        self.update_path_labels()
        self.load_recent_image()
        
        # 保存配置
        self.save_config()
    
    def open_annotation_dir(self):
        """打开标注文件"""
        dir_path = QFileDialog.getExistingDirectory(self, "选择coco格式标注文件")
        if not dir_path:
            return   
        self.annotation_dir = dir_path
        self.annotation_files = [f for f in os.listdir(dir_path) 
                           if f.lower().endswith(('.json', '.JSON'))] 
        if not self.annotation_files:
            QMessageBox.critical(self, "错误", "选择的文件夹中没有json文件")
            return
        self.update_cap_bbox_path()
        self.update_path_labels()
        self.status_bar.showMessage(f"标注文件夹已设置: {os.path.abspath(self.annotation_dir)}")
        
        # 保存配置
        self.save_config()
    
    def save_current_annotation(self):
        """保存当前图像的标注到内存中"""
        if not self.image_files or not self.modified:
            return
        image_key = self.image_files[self.current_image_index]
        # 确保当前图像的注解字典存在
        if image_key not in self.annotations:
            self.annotations[image_key] = {
                "description": "",
                "qa_pairs": []
            }
        
        # 保存描述内容
        self.annotations[image_key]["description"] = self.desc_text.toPlainText().strip()
        
        # 保存问答对
        self.annotations[image_key]["qa_pairs"] = self.collect_qa_pairs()
        
        self.modified = False
    
    def collect_qa_pairs(self):
        """收集当前所有的问答对"""
        qa_pairs = []
        
        # 遍历所有问答对框架
        for i in range(self.qa_container_layout.count()):
            qa_frame = self.qa_container_layout.itemAt(i).widget()
            question = qa_frame.question_text.toPlainText().strip()
            answer = qa_frame.answer_text.toPlainText().strip()
            
            # 只有有问题或答案时才保存
            if question or answer:
                qa_pairs.append({
                    "question": question,
                    "answer": answer
                })
        
        return qa_pairs
    
    def save_annotations(self):
        """保存标注到文件"""
        self.save_current_annotation()
        
        if not self.annotations:
            QMessageBox.information(self, "提示", "没有要保存的标注数据")
            return
        
        # 如果没有保存路径，使用原JSON文件名加上_refine.json
        if not self.save_path and self.json_file_path:
            base_name = os.path.splitext(os.path.basename(self.json_file_path))[0]
            self.save_path = os.path.join(os.path.dirname(self.json_file_path), f"{base_name}_refine.json")
        
        if not self.save_path:
            self.save_annotations_as()
            return
        
        try:
            # 确保输出目录存在
            os.makedirs(os.path.dirname(self.save_path), exist_ok=True)
            
            # 创建要保存的数据结构
            save_data = []
            
            for image_file, annotation in self.annotations.items():
                # 获取原始JSON数据（如果存在）
                image_data = self.get_image_data(image_file)
                
                # 创建新的对话记录
                conversations = []
                
                # 添加图像描述
                if annotation["description"]:
                    conversations.append({
                        "from": "human",
                        "value": "从专业角度描述这张图像。"
                    })
                    conversations.append({
                        "from": "gpt",
                        "value": annotation["description"]
                    })
                
                # 添加问答对
                for qa_pair in annotation["qa_pairs"]:
                    conversations.append({
                        "from": "human",
                        "value": qa_pair["question"]
                    })
                    conversations.append({
                        "from": "gpt",
                        "value": qa_pair["answer"]
                    })
                
                # 创建新的条目
                new_entry = {
                    "id": os.path.splitext(image_file)[0],
                    "image": os.path.join(self.image_dir, image_file),
                    "image_width": 0,  # 需要从图像获取
                    "image_height": 0,  # 需要从图像获取
                    "conversations": conversations
                }
                
                # 如果原始数据存在，保留部分字段
                if image_data:
                    new_entry["image_width"] = image_data.get("image_width", 0)
                    new_entry["image_height"] = image_data.get("image_height", 0)
                
                save_data.append(new_entry)
            
            # 保存到文件
            with open(self.save_path, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, ensure_ascii=False, indent=2)
            
            # 更新保存路径标签
            self.save_path_label.setText(f"保存路径: {os.path.abspath(self.save_path)}")
            
            QMessageBox.information(
                self,
                "保存成功",
                f"文件已保存到:\n{os.path.abspath(self.save_path)}"
            )
            self.modified = False
            
            # 保存配置
            self.save_config()
        except Exception as e:
            QMessageBox.critical(self, "保存错误", f"无法保存文件: {str(e)}")
    
    def save_annotations_as(self):
        """另存为标注文件"""
        if not self.annotations:
            QMessageBox.information(self, "提示", "没有要保存的标注数据")
            return
        
        # 设置默认文件名
        default_name = ""
        if self.json_file_path:
            base_name = os.path.splitext(os.path.basename(self.json_file_path))[0]
            default_name = f"{base_name}_refine.json"
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "保存标注文件",
            default_name,
            "JSON文件 (*.json);;所有文件 (*)"
        )
        
        if not file_path:
            return
        
        self.save_path = file_path
        self.save_annotations()
    
    def confirm_exit(self):
        """退出前确认保存"""
        # 保存当前配置
        self.save_config()
        
        if self.modified:
            reply = QMessageBox.question(
                self,
                "退出",
                "有未保存的修改，是否保存后退出？",
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel
            )
            
            if reply == QMessageBox.Yes:
                self.save_annotations()
                self.close()
            elif reply == QMessageBox.No:
                self.close()
        else:
            self.close()
    
    def zoom_in(self):
        """放大图像"""
        if hasattr(self, 'current_image') and self.current_image:
            self.current_image = self.current_image.resize(
                (int(self.current_image.width * 1.1), int(self.current_image.height * 1.1)),
                Image.LANCZOS
            )
            self.display_image(self.current_image)
    
    def zoom_out(self):
        """缩小图像"""
        if hasattr(self, 'current_image') and self.current_image:
            self.current_image = self.current_image.resize(
                (int(self.current_image.width * 0.9), int(self.current_image.height * 0.9)),
                Image.LANCZOS
            )
            self.display_image(self.current_image)
    
    def reset_zoom(self):
        """重置图像缩放"""
        if hasattr(self, 'current_image') and self.current_image:
            image_path = os.path.join(self.image_dir, self.image_files[self.current_image_index])
            self.load_recent_image()
    
    def show_help(self):
        """显示帮助信息"""
        help_text = """图像文本标注工具使用说明 v2.1
1. 基本功能
   - 支持查看和编辑遥感图像的文本描述
   - 支持管理和编辑图像相关的问答对
   - 支持从JSON文件加载描述和问答对
   - 支持批量处理多张图像
   - 支持保存为JSON格式的标注文件
   - 支持在图像上显示检测框（需提供标注文件夹）
2. 图像加载与浏览
   - 点击"文件"菜单 > "打开图像文件夹" 选择包含图像的文件夹
   - 使用工具栏的"上一张 (←/↑)"、"下一张 (→/↓)"按钮浏览图像
   - 在"查看"菜单中也可找到"上一张"和"下一张"选项
   - 状态栏显示当前图像位置（如 3/10）
   - 图像下方显示当前图像文件的绝对路径
3. 图像描述管理
   - 点击"添加图像描述"按钮可选择：
     * "添加空白的图像描述"：创建新的空白描述
     * "读取已有的图像描述"：从JSON文件加载已有描述
     * "VLM生成图像描述"：调用视觉语言模型自动生成描述
   - 描述文本框下方显示描述来源：
     * 用户手动添加
     * VLM生成
     * JSON文件路径
   - 使用"删除图像描述"按钮清除当前描述
4. 视觉问答对管理
   - 点击"添加视觉问答对"按钮可选择：
     * "添加空白的视觉问答对"：创建新的空白问答对
     * "读取已有的视觉问答对"：从JSON文件加载已有问答
     * "VLM生成视觉问答对"：调用视觉语言模型自动生成问答
   - 问答区域下方显示问答来源：
     * 用户手动添加
     * VLM生成
     * JSON文件路径
   - 每个问答对可单独编辑或删除
   - 使用"删除视觉问答对"按钮清除所有问答
5. VLM辅助标注
   - 在"文件"菜单 > "设置API"中配置：
     * API地址（本地默认：http://localhost:8089/v1）
     * API密钥（本地调用使用：no-api-key-required）
   - 生成描述/问答时会弹出提示词编辑窗口
   - 可修改默认提示词以获得更精准的结果
   - 生成过程中状态栏显示处理状态
6. 检测框显示
   - 点击工具栏的"显示检测框"按钮在图像上显示目标检测框
   - 点击"不显示检测框"按钮隐藏检测框
   - 使用前需先在"文件"菜单中选择标注文件夹
   - 检测框数据需为JSON格式，包含"bboxes"字段
7. 图像查看调整
   - 使用"查看"菜单中的选项：
     * "放大图像"：放大当前图像（快捷键无）
     * "缩小图像"：缩小当前图像（快捷键无）
     * "实际大小"：恢复原始大小（快捷键无）
8. 保存功能
   - 点击"保存 (Ctrl+S)"按钮保存当前所有标注
   - 首次保存或使用"另存为"可选择保存位置
   - 保存后底部显示JSON文件的绝对路径
   - 默认保存为原JSON文件名加上_refine.json
9. 断点续查功能
   - 点击工具栏的"断点续查"按钮可恢复上次查看的位置
   - 程序会自动记录当前查看的图像索引
   - 退出程序后再次打开会自动加载上次进度
10. 进度显示
   - 工具栏显示当前查看进度（如 3/10）
   - 进度条实时显示当前查看位置和百分比
   - 每查看一个图-文对，进度条都会更新
提示与技巧：
   - 每张图像的编辑会自动暂存到内存中
   - 切换图像前建议保存当前修改
   - VLM生成内容后仍可手动编辑优化
   - 保存的JSON文件可直接用于模型训练
   - 使用方向键可快速切换图像（左/上：上一张，右/下：下一张）
   - 显示检测框前请确保已选择标注文件夹
   - 使用断点续查功能可快速回到上次工作位置
常见问题：
   - 无法加载图像？检查图像格式是否支持（PNG/JPG等）
   - VLM生成失败？检查API配置和网络连接
   - 描述/问答未保存？切换图像前需手动保存
   - 找不到保存文件？查看底部的保存路径信息
   - 无法显示检测框？检查是否已选择标注文件夹
   - 断点续查无效？检查配置文件是否可写
版本信息：
   多模态（图像-文本）标注查验工具 v2.1
   作者: LX
   创建日期: 2025年07月"""
        
        help_dialog = QDialog(self)
        help_dialog.setWindowTitle("使用帮助")
        help_dialog.setGeometry(100, 100, 500, 600)
        
        layout = QVBoxLayout(help_dialog)
        
        text_edit = QTextEdit()
        text_edit.setPlainText(help_text)
        text_edit.setReadOnly(True)
        layout.addWidget(text_edit)
        
        btn_close = QPushButton("关闭")
        btn_close.clicked.connect(help_dialog.accept)
        layout.addWidget(btn_close)
        
        help_dialog.exec_()
    
    def show_about(self):
        """显示关于信息"""
        about_text = """图像文本标注工具 v2.1
        
功能：
   - 查看和编辑图像描述
   - 管理和编辑图文问答
   - 从JSON文件加载描述和问答对
   - VLM辅助标注（描述生成和问答对生成）
   - 批量处理多张图像
   - 保存为JSON标注文件
   - 支持在图像上显示检测框
   - 断点续查功能
   - 实时进度显示（含百分比）
作者: LX
创建日期: 2025年07月"""
        QMessageBox.about(self, "关于", about_text)


class ImageLoader(QThread):
    """用于在后台加载图像的线程"""
    image_loaded = pyqtSignal(object)
    
    def __init__(self, image_path):
        super().__init__()
        self.image_path = image_path
    
    def run(self):
        try:
            image = Image.open(self.image_path)
            # 限制最大尺寸
            max_size = 3000
            if image.width > max_size or image.height > max_size:
                ratio = min(max_size / image.width, max_size / image.height)
                new_size = (int(image.width * ratio), int(image.height * ratio))
                image = image.resize(new_size, Image.LANCZOS)
            
            self.image_loaded.emit(image)
        except Exception as e:
            self.image_loaded.emit(None)
        

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # 设置应用字体
    font = QFont("Noto Sans CJK SC", 10)
    app.setFont(font)
    
    window = ImageTextAnnotator()
    window.show()
    sys.exit(app.exec_())
