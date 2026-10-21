import os
import sys
import json
import datetime
import base64
import io
import re
import argparse
import shutil
import threading
import queue
from tqdm import tqdm
from openai import OpenAI, BadRequestError
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QLineEdit, QPushButton, QLabel, QTextEdit, QFileDialog, QProgressBar,
    QShortcut, QGroupBox, QSizePolicy, QFrame, QMenu, QAction, QMessageBox,
    QStackedWidget, QToolBar, QScrollArea, QListWidget, QInputDialog, QComboBox,
    QListWidgetItem, QStatusBar, QSizeGrip
)
from PyQt5.QtGui import (
    QPixmap, QImage, QPainter, QPen, QColor, QKeySequence, QFont, QIcon, 
    QPalette, QLinearGradient, QBrush, QMovie
)
from PyQt5.QtCore import (
    Qt, QPoint, QThread, pyqtSignal, QSize, QPropertyAnimation, QEasingCurve,
    QTimer
)
from PIL import Image, ImageDraw

# ========================================================
# 侧边栏按钮类
# ========================================================
class SidebarButton(QPushButton):
    def __init__(self, icon_path, text, parent=None):
        super().__init__(text, parent)
        self.setFixedHeight(60)
        self.setIcon(QIcon(icon_path))
        self.setIconSize(QSize(32, 32))
        self.setStyleSheet("""
            QPushButton {
                background-color: rgba(30, 30, 50, 180);
                color: #e0e0ff;
                border: 1px solid #4a4a7a;
                border-radius: 8px;
                padding: 10px;
                text-align: left;
                font-size: 14px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: rgba(50, 50, 80, 200);
                border: 1px solid #6a6aaa;
            }
            QPushButton:pressed {
                background-color: rgba(70, 70, 120, 220);
            }
            QPushButton:checked {
                background-color: rgba(80, 120, 200, 220);
                border: 1px solid #8ab4f8;
            }
        """)
        self.setCheckable(True)
        self.setCursor(Qt.PointingHandCursor)

# ========================================================
# 高科技感标题栏
# ========================================================
class TechTitleBar(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.setFixedHeight(40)
        self.setStyleSheet("background-color: rgba(20, 20, 40, 220);")
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 0, 10, 0)
        layout.setSpacing(10)
        
        # # Logo和标题
        # self.logo = QLabel()
        # self.logo.setPixmap(QPixmap("CASC-LOGO.png").scaled(30, 30, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        # layout.addWidget(self.logo)
        
        self.title = QLabel("多模态大模型训练数据管理平台")
        self.title.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: #8ab4f8;
            background: transparent;
        """)
        layout.addWidget(self.title)
        
        # 添加动画效果
        self.title_animation = QPropertyAnimation(self.title, b"opacity")
        self.title_animation.setDuration(2000)
        self.title_animation.setStartValue(0.5)
        self.title_animation.setEndValue(1.0)
        self.title_animation.setEasingCurve(QEasingCurve.InOutQuad)
        self.title_animation.setLoopCount(-1)
        self.title_animation.start()
        
        layout.addStretch()
        
        # 系统按钮
        self.minimize_btn = QPushButton("─")
        self.minimize_btn.setFixedSize(30, 30)
        self.minimize_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #aaaaaa;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(100, 100, 150, 100);
                color: #ffffff;
            }
        """)
        self.minimize_btn.clicked.connect(self.parent.showMinimized)
        
        self.close_btn = QPushButton("✕")
        self.close_btn.setFixedSize(30, 30)
        self.close_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #aaaaaa;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(200, 50, 50, 150);
                color: #ffffff;
            }
        """)
        self.close_btn.clicked.connect(self.parent.close)
        
        layout.addWidget(self.minimize_btn)
        layout.addWidget(self.close_btn)

# ========================================================
# 主窗口类
# ========================================================
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("多模态大模型训练数据管理平台")
        self.setGeometry(100, 100, 1400, 900)
        self.setWindowIcon(QIcon("CASC-LOGO.png"))
        self.setStyleSheet("background-color: #0a0a14;")
        
        # 自定义标题栏
        self.title_bar = TechTitleBar(self)
        self.setMenuWidget(self.title_bar)
        
        # 创建主布局
        self.main_widget = QWidget()
        self.main_layout = QHBoxLayout(self.main_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        self.setCentralWidget(self.main_widget)
        
        # 创建侧边栏
        self.create_sidebar()
        
        # 创建主内容区域
        self.create_main_content()
        
        # 添加底部状态栏
        self.create_status_bar()
        
        # 添加背景动画
        self.setup_background_animation()
    
    def setup_background_animation(self):
        # 创建背景动画效果
        self.animation_timer = QTimer(self)
        self.animation_timer.timeout.connect(self.update_background)
        self.animation_timer.start(50)
        self.animation_step = 0
    
    def update_background(self):
        self.animation_step = (self.animation_step + 1) % 100
        self.main_widget.update()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 绘制科技感背景
        bg_color = QColor(10, 10, 20)
        painter.fillRect(self.rect(), bg_color)
        
        # 绘制网格
        grid_color = QColor(30, 30, 50, 40)
        painter.setPen(grid_color)
        
        step = 20
        for x in range(0, self.width(), step):
            painter.drawLine(x, 0, x, self.height())
        for y in range(0, self.height(), step):
            painter.drawLine(0, y, self.width(), y)
        
        # 绘制动态粒子效果
        particle_color = QColor(80, 120, 200, 80)
        painter.setPen(Qt.NoPen)
        painter.setBrush(particle_color)
        
        for i in range(50):
            x = (self.animation_step * 2 + i * 37) % self.width()
            y = (self.animation_step * 3 + i * 29) % self.height()
            size = 2 + (i % 3)
            painter.drawEllipse(QPoint(x, y), size, size)
    
    def create_sidebar(self):
        # 侧边栏
        self.sidebar = QFrame()
        self.sidebar.setFixedWidth(220)
        self.sidebar.setStyleSheet("""
            background-color: rgba(20, 20, 35, 200);
            border-right: 1px solid #333355;
        """)
        
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(10, 20, 10, 20)
        sidebar_layout.setSpacing(15)
        
        # 平台标题
        title = QLabel("数据管理平台")
        title.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: #8ab4f8;
            padding: 10px;
            border-bottom: 1px solid #333355;
        """)
        title.setAlignment(Qt.AlignCenter)
        sidebar_layout.addWidget(title)
        
        # 添加按钮
        self.btn_data_select = SidebarButton("icons/data_select.png", "图像数据筛选")
        self.btn_data_select.clicked.connect(lambda: self.switch_page(0))
        
        self.btn_data_cap_vqa = SidebarButton("icons/data_cap_vqa.png", "视觉-语言任务衍生数据生成")
        self.btn_data_cap_vqa.clicked.connect(lambda: self.switch_page(1))
        
        self.btn_data_refine = SidebarButton("icons/data_refine.png", "视觉-语言任务衍生数据校正")
        self.btn_data_refine.clicked.connect(lambda: self.switch_page(2))
        
        sidebar_layout.addWidget(self.btn_data_select)
        sidebar_layout.addWidget(self.btn_data_cap_vqa)
        sidebar_layout.addWidget(self.btn_data_refine)
        
        sidebar_layout.addStretch()
        
        # 添加版本信息
        version = QLabel("v1.0")
        version.setStyleSheet("color: #6a6a8a; font-size: 12px;")
        version.setAlignment(Qt.AlignCenter)
        sidebar_layout.addWidget(version)
        
        self.main_layout.addWidget(self.sidebar)
    
    def create_main_content(self):
        # 主内容区域
        self.content_frame = QFrame()
        self.content_frame.setStyleSheet("background-color: rgba(15, 15, 25, 180);")
        
        content_layout = QVBoxLayout(self.content_frame)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        
        # 创建堆叠窗口
        self.stacked_widget = QStackedWidget()
        self.stacked_widget.setStyleSheet("background: transparent;")
        
        # 添加三个功能页面
        self.data_select_widget = DataSelectWidget()
        self.data_cap_vqa_widget = DataCapVqaWidget()
        self.data_refine_widget = DataRefineWidget()
        
        self.stacked_widget.addWidget(self.data_select_widget)
        self.stacked_widget.addWidget(self.data_cap_vqa_widget)
        self.stacked_widget.addWidget(self.data_refine_widget)
        
        content_layout.addWidget(self.stacked_widget)
        
        self.main_layout.addWidget(self.content_frame, 1)
    
    def create_status_bar(self):
        # 状态栏
        self.status_bar = QStatusBar()
        self.status_bar.setStyleSheet("""
            background-color: rgba(20, 20, 35, 220);
            color: #8a8aaa;
            border-top: 1px solid #333355;
            font-size: 12px;
        """)
        
        # 添加状态标签
        self.status_label = QLabel("就绪")
        self.status_bar.addWidget(self.status_label, 1)
        
        # 添加系统信息
        self.sys_info_label = QLabel("")
        self.status_bar.addPermanentWidget(self.sys_info_label)
        
        self.setStatusBar(self.status_bar)
        
        # 更新系统信息
        self.update_sys_info()
    
    def update_sys_info(self):
        # 更新系统信息
        self.sys_info_label.setText("多模态数据管理平台 | 智能前沿所")
    
    def switch_page(self, index):
        # 切换页面
        self.stacked_widget.setCurrentIndex(index)
        
        # 更新按钮状态
        self.btn_data_select.setChecked(index == 0)
        self.btn_data_cap_vqa.setChecked(index == 1)
        self.btn_data_refine.setChecked(index == 2)
        
        # 更新状态栏
        pages = ["图像数据筛选", "视觉-语言任务衍生数据生成", "视觉-语言任务衍生数据校正"]
        self.status_label.setText(f"当前页面: {pages[index]}")

# ========================================================
# 图像数据筛选模块 (基于data_select.py)
# ========================================================
class DataSelectWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.setup_style()
    
    def setup_style(self):
        self.setStyleSheet("""
            QGroupBox {
                border: 1px solid #444466;
                border-radius: 8px;
                margin-top: 1em;
                padding-top: 10px;
                background-color: rgba(30, 30, 50, 180);
                color: #c0c0e0;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QLabel {
                color: #c0c0e0;
            }
            QPushButton {
                background-color: rgba(60, 60, 100, 200);
                color: #e0e0ff;
                border: 1px solid #4a4a7a;
                border-radius: 4px;
                padding: 5px 10px;
            }
            QPushButton:hover {
                background-color: rgba(80, 80, 130, 220);
                border: 1px solid #6a6aaa;
            }
            QPushButton:pressed {
                background-color: rgba(100, 100, 160, 240);
            }
            QLineEdit, QTextEdit {
                background-color: rgba(25, 25, 40, 200);
                color: #e0e0ff;
                border: 1px solid #444466;
                border-radius: 4px;
                padding: 5px;
            }
            QProgressBar {
                border: 1px solid #444466;
                border-radius: 4px;
                text-align: center;
                background-color: rgba(20, 20, 35, 200);
            }
            QProgressBar::chunk {
                background-color: #4a86e8;
                border-radius: 4px;
            }
        """)
    
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # 标题
        title = QLabel("图像数据（已标&未标）高质量筛选")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #8ab4f8;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # 路径选择区域
        path_group = QGroupBox("数据路径设置")
        path_layout = QHBoxLayout()
        
        # 图像路径
        images_group = QGroupBox("图像路径")
        images_layout = QVBoxLayout()
        self.images_path_label = QLabel("未选择")
        images_layout.addWidget(self.images_path_label)
        
        images_btn = QPushButton("选择图像文件夹")
        images_btn.clicked.connect(self.select_images_path)
        images_layout.addWidget(images_btn)
        
        images_group.setLayout(images_layout)
        
        # 标签路径
        labels_group = QGroupBox("标签路径")
        labels_layout = QVBoxLayout()
        self.labels_path_label = QLabel("未选择")
        labels_layout.addWidget(self.labels_path_label)
        
        labels_btn = QPushButton("选择标签文件夹")
        labels_btn.clicked.connect(self.select_labels_path)
        labels_layout.addWidget(labels_btn)
        
        labels_group.setLayout(labels_layout)
        
        path_layout.addWidget(images_group, 1)
        path_layout.addWidget(labels_group, 1)
        path_group.setLayout(path_layout)
        layout.addWidget(path_group)
        
        # 搜索区域
        search_group = QGroupBox("数据筛选")
        search_layout = QVBoxLayout()
        
        # 搜索输入
        search_input_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("输入搜索关键词（如'商业客机'），留空则提取所有文件")
        search_input_layout.addWidget(self.search_input, 4)
        
        self.search_button = QPushButton("开始搜索")
        self.search_button.clicked.connect(self.start_search)
        search_input_layout.addWidget(self.search_button, 1)
        
        search_layout.addLayout(search_input_layout)
        
        # 去重按钮
        dedup_layout = QHBoxLayout()
        self.dedup_button = QPushButton("算法去重（开发中）")
        self.dedup_button.setToolTip("使用算法去除重复图像")
        dedup_layout.addWidget(self.dedup_button)
        
        self.load_dedup_button = QPushButton("读取算法去重结果")
        self.load_dedup_button.setToolTip("读取算法去重结果的JSON文件")
        dedup_layout.addWidget(self.load_dedup_button)
        
        dedup_layout.addStretch()
        search_layout.addLayout(dedup_layout)
        search_group.setLayout(search_layout)
        layout.addWidget(search_group)
        
        # 显示区域
        display_group = QGroupBox("数据预览")
        display_layout = QHBoxLayout()
        
        # 图像预览
        image_group = QGroupBox("图像预览")
        image_layout = QVBoxLayout()
        
        self.image_display = QLabel()
        self.image_display.setAlignment(Qt.AlignCenter)
        self.image_display.setMinimumSize(400, 300)
        self.image_display.setStyleSheet("border: 1px solid #444466; background-color: rgba(20, 20, 35, 200);")
        
        self.image_filename_label = QLabel("图像文件名: ")
        self.image_filename_label.setAlignment(Qt.AlignCenter)
        
        image_layout.addWidget(self.image_display, 3)
        image_layout.addWidget(self.image_filename_label, 1)
        image_group.setLayout(image_layout)
        
        # JSON预览
        json_group = QGroupBox("标签详情")
        json_layout = QVBoxLayout()
        
        self.json_display = QTextEdit()
        self.json_display.setReadOnly(True)
        
        self.json_filename_label = QLabel("标签文件名: ")
        self.json_filename_label.setAlignment(Qt.AlignCenter)
        
        json_layout.addWidget(self.json_display, 3)
        json_layout.addWidget(self.json_filename_label, 1)
        json_group.setLayout(json_layout)
        
        display_layout.addWidget(image_group, 1)
        display_layout.addWidget(json_group, 1)
        display_group.setLayout(display_layout)
        layout.addWidget(display_group, 1)
        
        # 控制区域
        control_group = QGroupBox("数据操作")
        control_layout = QVBoxLayout()
        
        # 进度条
        progress_layout = QHBoxLayout()
        self.progress_label = QLabel("0/0")
        self.progress_label.setFixedWidth(80)
        self.progress_bar = QProgressBar()
        self.progress_bar.setFormat("%p% (%v/%m)")
        progress_layout.addWidget(self.progress_label)
        progress_layout.addWidget(self.progress_bar)
        control_layout.addLayout(progress_layout)
        
        # 导航按钮
        nav_layout = QHBoxLayout()
        self.prev_button = QPushButton("上一张 (←/↑)")
        self.prev_button.setEnabled(False)
        nav_layout.addWidget(self.prev_button)
        
        self.next_button = QPushButton("下一张 (→/↓)")
        self.next_button.setEnabled(False)
        nav_layout.addWidget(self.next_button)
        control_layout.addLayout(nav_layout)
        
        # 操作按钮
        action_layout = QHBoxLayout()
        self.save_button = QPushButton("保存当前图像 (Ctrl+S)")
        self.save_button.setEnabled(False)
        action_layout.addWidget(self.save_button)
        
        self.discard_button = QPushButton("不保存并剔除 (Del/Backs)")
        self.discard_button.setEnabled(False)
        action_layout.addWidget(self.discard_button)
        control_layout.addLayout(action_layout)
        
        # 检测框按钮
        bbox_layout = QHBoxLayout()
        self.show_bbox_button = QPushButton("显示检测框")
        bbox_layout.addWidget(self.show_bbox_button)
        
        self.hide_bbox_button = QPushButton("隐藏检测框")
        bbox_layout.addWidget(self.hide_bbox_button)
        control_layout.addLayout(bbox_layout)
        
        control_group.setLayout(control_layout)
        layout.addWidget(control_group)
        
        self.setLayout(layout)
    
    def select_images_path(self):
        path = QFileDialog.getExistingDirectory(self, "选择图像文件夹")
        if path:
            self.images_path_label.setText(path)
    
    def select_labels_path(self):
        path = QFileDialog.getExistingDirectory(self, "选择标签文件夹")
        if path:
            self.labels_path_label.setText(path)
    
    def start_search(self):
        # 模拟搜索过程
        self.progress_bar.setRange(0, 100)
        
        # 创建动画效果
        self.animation = QPropertyAnimation(self.progress_bar, b"value")
        self.animation.setDuration(2000)
        self.animation.setStartValue(0)
        self.animation.setEndValue(100)
        self.animation.setEasingCurve(QEasingCurve.InOutQuad)
        self.animation.start()
        
        # 启用按钮
        self.prev_button.setEnabled(True)
        self.next_button.setEnabled(True)
        self.save_button.setEnabled(True)
        self.discard_button.setEnabled(True)
        
        # 显示示例图像
        pixmap = QPixmap("example_image.jpg")
        if not pixmap.isNull():
            self.image_display.setPixmap(pixmap.scaled(
                self.image_display.width(), 
                self.image_display.height(),
                Qt.KeepAspectRatio, 
                Qt.SmoothTransformation
            ))
        
        # 显示示例JSON
        example_json = {
            "filename": "example_image.jpg",
            "annotations": [
                {
                    "class": "airplane",
                    "label": "commercial",
                    "coordinates": "100,200,300,400"
                }
            ]
        }
        self.json_display.setPlainText(json.dumps(example_json, indent=2))

# ========================================================
# 视觉-语言任务衍生数据生成模块 (基于data_cap_vqa.py)
# ========================================================
class DataCapVqaWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.setup_style()
    
    def setup_style(self):
        self.setStyleSheet("""
            QGroupBox {
                border: 1px solid #444466;
                border-radius: 8px;
                margin-top: 1em;
                padding-top: 10px;
                background-color: rgba(30, 30, 50, 180);
                color: #c0c0e0;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QLabel {
                color: #c0c0e0;
            }
            QPushButton {
                background-color: rgba(60, 60, 100, 200);
                color: #e0e0ff;
                border: 1px solid #4a4a7a;
                border-radius: 4px;
                padding: 5px 10px;
            }
            QPushButton:hover {
                background-color: rgba(80, 80, 130, 220);
                border: 1px solid #6a6aaa;
            }
            QPushButton:pressed {
                background-color: rgba(100, 100, 160, 240);
            }
            QLineEdit, QTextEdit {
                background-color: rgba(25, 25, 40, 200);
                color: #e0e0ff;
                border: 1px solid #444466;
                border-radius: 4px;
                padding: 5px;
            }
            QProgressBar {
                border: 1px solid #444466;
                border-radius: 4px;
                text-align: center;
                background-color: rgba(20, 20, 35, 200);
            }
            QProgressBar::chunk {
                background-color: #4a86e8;
                border-radius: 4px;
            }
        """)
    
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # 标题
        title = QLabel("视觉-语言任务衍生数据生成 (Image Caption & Visual QA)")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #8ab4f8;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # 开发中提示
        dev_label = QLabel("功能开发中")
        dev_label.setStyleSheet("font-size: 16px; color: #ffaa44; font-weight: bold;")
        dev_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(dev_label)
        
        # 配置区域
        config_group = QGroupBox("模型配置")
        config_layout = QVBoxLayout()
        
        # API设置
        api_layout = QHBoxLayout()
        api_layout.addWidget(QLabel("API地址:"))
        self.api_url_edit = QLineEdit("http://localhost:8089/v1")
        api_layout.addWidget(self.api_url_edit, 3)
        
        api_layout.addWidget(QLabel("API密钥:"))
        self.api_key_edit = QLineEdit("no-api-key-required")
        api_layout.addWidget(self.api_key_edit, 2)
        config_layout.addLayout(api_layout)
        
        # 模型选择
        model_layout = QHBoxLayout()
        model_layout.addWidget(QLabel("模型选择:"))
        self.model_combo = QComboBox()
        self.model_combo.addItems(["InternVL3-8B", "InternVL2-6B", "InternVL1-5B"])
        model_layout.addWidget(self.model_combo, 2)
        
        model_layout.addStretch(1)
        config_layout.addLayout(model_layout)
        
        config_group.setLayout(config_layout)
        layout.addWidget(config_group)
        
        # 数据设置
        data_group = QGroupBox("数据设置")
        data_layout = QVBoxLayout()
        
        # 图像文件夹
        img_layout = QHBoxLayout()
        img_layout.addWidget(QLabel("图像文件夹:"))
        self.img_path_edit = QLineEdit()
        img_layout.addWidget(self.img_path_edit, 3)
        
        img_btn = QPushButton("浏览")
        img_btn.clicked.connect(self.select_img_path)
        img_layout.addWidget(img_btn, 1)
        data_layout.addLayout(img_layout)
        
        # 标签文件夹
        label_layout = QHBoxLayout()
        label_layout.addWidget(QLabel("标签文件夹:"))
        self.label_path_edit = QLineEdit()
        label_layout.addWidget(self.label_path_edit, 3)
        
        label_btn = QPushButton("浏览")
        label_btn.clicked.connect(self.select_label_path)
        label_layout.addWidget(label_btn, 1)
        data_layout.addLayout(label_layout)
        
        # 输出文件夹
        output_layout = QHBoxLayout()
        output_layout.addWidget(QLabel("输出文件夹:"))
        self.output_path_edit = QLineEdit()
        output_layout.addWidget(self.output_path_edit, 3)
        
        output_btn = QPushButton("浏览")
        output_btn.clicked.connect(self.select_output_path)
        output_layout.addWidget(output_btn, 1)
        data_layout.addLayout(output_layout)
        
        # 处理参数
        param_layout = QHBoxLayout()
        param_layout.addWidget(QLabel("分块大小:"))
        self.chunk_size_edit = QLineEdit("1024")
        param_layout.addWidget(self.chunk_size_edit)
        
        param_layout.addWidget(QLabel("分块数量:"))
        self.chunk_num_edit = QLineEdit("5")
        param_layout.addWidget(self.chunk_num_edit)
        
        param_layout.addStretch()
        data_layout.addLayout(param_layout)
        
        data_group.setLayout(data_layout)
        layout.addWidget(data_group)
        
        # 处理控制
        process_group = QGroupBox("处理控制")
        process_layout = QVBoxLayout()
        
        # 提示词
        prompt_layout = QHBoxLayout()
        prompt_layout.addWidget(QLabel("提示词:"))
        self.prompt_edit = QTextEdit()
        self.prompt_edit.setPlainText(
            "请详细描述这张图像的内容，包括主要物体、场景、颜色、动作和物体间的相互关系等元素。要求描述细致准确，重点关注军事情报相关信息。"
        )
        self.prompt_edit.setMaximumHeight(80)
        prompt_layout.addWidget(self.prompt_edit, 1)
        process_layout.addLayout(prompt_layout)
        
        # 按钮区域
        btn_layout = QHBoxLayout()
        self.start_btn = QPushButton("开始生成")
        self.start_btn.setStyleSheet("background-color: rgba(80, 150, 80, 200);")
        btn_layout.addWidget(self.start_btn)
        
        self.stop_btn = QPushButton("停止生成")
        self.stop_btn.setStyleSheet("background-color: rgba(180, 80, 80, 200);")
        self.stop_btn.setEnabled(False)
        btn_layout.addWidget(self.stop_btn)
        process_layout.addLayout(btn_layout)
        
        # 进度条
        progress_layout = QHBoxLayout()
        self.progress_label = QLabel("就绪")
        progress_layout.addWidget(self.progress_label)
        
        self.progress_bar = QProgressBar()
        progress_layout.addWidget(self.progress_bar)
        process_layout.addLayout(progress_layout)
        
        # 日志显示
        log_layout = QVBoxLayout()
        log_layout.addWidget(QLabel("处理日志:"))
        
        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        log_layout.addWidget(self.log_display)
        process_layout.addLayout(log_layout)
        
        process_group.setLayout(process_layout)
        layout.addWidget(process_group, 1)
        
        self.setLayout(layout)
    
    def select_img_path(self):
        path = QFileDialog.getExistingDirectory(self, "选择图像文件夹")
        if path:
            self.img_path_edit.setText(path)
    
    def select_label_path(self):
        path = QFileDialog.getExistingDirectory(self, "选择标签文件夹")
        if path:
            self.label_path_edit.setText(path)
    
    def select_output_path(self):
        path = QFileDialog.getExistingDirectory(self, "选择输出文件夹")
        if path:
            self.output_path_edit.setText(path)
    
    def start_generation(self):
        # 模拟生成过程
        self.log_display.append("开始处理图像数据...")
        self.progress_bar.setRange(0, 100)
        
        # 创建动画效果
        self.animation = QPropertyAnimation(self.progress_bar, b"value")
        self.animation.setDuration(5000)
        self.animation.setStartValue(0)
        self.animation.setEndValue(100)
        self.animation.setEasingCurve(QEasingCurve.InOutQuad)
        self.animation.start()
        
        # 更新日志
        self.log_display.append("加载模型: InternVL3-8B...")
        self.log_display.append("处理图像块 1/5...")
        self.log_display.append("生成描述: 图像中包含多架商业客机停放在机场...")
        self.log_display.append("生成问答对: Q: 机场上有多少架飞机? A: 机场上共有12架飞机...")
        self.log_display.append("处理图像块 2/5...")
        self.log_display.append("处理完成! 共生成1200个描述和问答对")

# ========================================================
# 视觉-语言任务衍生数据高质量校正模块 (基于data_refine.py)
# ========================================================
class DataRefineWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.setup_style()
    
    def setup_style(self):
        self.setStyleSheet("""
            QGroupBox {
                border: 1px solid #444466;
                border-radius: 8px;
                margin-top: 1em;
                padding-top: 10px;
                background-color: rgba(30, 30, 50, 180);
                color: #c0c0e0;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QLabel {
                color: #c0c0e0;
            }
            QPushButton {
                background-color: rgba(60, 60, 100, 200);
                color: #e0e0ff;
                border: 1px solid #4a4a7a;
                border-radius: 4px;
                padding: 5px 10px;
            }
            QPushButton:hover {
                background-color: rgba(80, 80, 130, 220);
                border: 1px solid #6a6aaa;
            }
            QPushButton:pressed {
                background-color: rgba(100, 100, 160, 240);
            }
            QLineEdit, QTextEdit {
                background-color: rgba(25, 25, 40, 200);
                color: #e0e0ff;
                border: 1px solid #444466;
                border-radius: 4px;
                padding: 5px;
            }
            QProgressBar {
                border: 1px solid #444466;
                border-radius: 4px;
                text-align: center;
                background-color: rgba(20, 20, 35, 200);
            }
            QProgressBar::chunk {
                background-color: #4a86e8;
                border-radius: 4px;
            }
            QScrollArea {
                border: 1px solid #444466;
                border-radius: 4px;
                background-color: rgba(25, 25, 40, 200);
            }
            QFrame {
                background-color: rgba(25, 25, 40, 200);
            }
        """)
    
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # 标题
        title = QLabel("视觉-语言任务衍生数据高质量校正")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #8ab4f8;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # 配置区域
        config_group = QGroupBox("数据配置")
        config_layout = QVBoxLayout()
        
        # 图像文件夹
        img_layout = QHBoxLayout()
        img_layout.addWidget(QLabel("图像文件夹:"))
        self.img_path_edit = QLineEdit()
        img_layout.addWidget(self.img_path_edit, 3)
        
        img_btn = QPushButton("浏览")
        img_btn.clicked.connect(self.select_img_path)
        img_layout.addWidget(img_btn, 1)
        config_layout.addLayout(img_layout)
        
        # 标注文件夹
        ann_layout = QHBoxLayout()
        ann_layout.addWidget(QLabel("标注文件夹:"))
        self.ann_path_edit = QLineEdit()
        ann_layout.addWidget(self.ann_path_edit, 3)
        
        ann_btn = QPushButton("浏览")
        ann_btn.clicked.connect(self.select_ann_path)
        ann_layout.addWidget(ann_btn, 1)
        config_layout.addLayout(ann_layout)
        
        # JSON文件
        json_layout = QHBoxLayout()
        json_layout.addWidget(QLabel("JSON文件:"))
        self.json_path_edit = QLineEdit()
        json_layout.addWidget(self.json_path_edit, 3)
        
        json_btn = QPushButton("浏览")
        json_btn.clicked.connect(self.select_json_path)
        json_layout.addWidget(json_btn, 1)
        config_layout.addLayout(json_layout)
        
        config_group.setLayout(config_layout)
        layout.addWidget(config_group)
        
        # 主显示区域
        main_display = QSplitter(Qt.Horizontal)
        
        # 左侧图像面板
        image_frame = QFrame()
        image_layout = QVBoxLayout(image_frame)
        
        # 图像显示区域
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setMinimumSize(400, 400)
        self.image_label.setStyleSheet("border: 1px solid #444466; background-color: rgba(20, 20, 35, 200);")
        
        # 滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidget(self.image_label)
        scroll_area.setWidgetResizable(True)
        image_layout.addWidget(scroll_area, 3)
        
        # 图像路径标签
        self.image_path_label = QLabel("图像路径: 尚未加载")
        image_layout.addWidget(self.image_path_label, 1)
        
        main_display.addWidget(image_frame)
        
        # 右侧文本面板
        text_frame = QFrame()
        text_layout = QVBoxLayout(text_frame)
        
        # 描述区域
        desc_label = QLabel("图像描述:")
        text_layout.addWidget(desc_label)
        
        self.desc_text = QTextEdit()
        self.desc_text.setMinimumHeight(100)
        text_layout.addWidget(self.desc_text, 1)
        
        # 描述来源标签
        self.desc_source_label = QLabel("描述来源: 尚未加载")
        text_layout.addWidget(self.desc_source_label)
        
        # 问答区域
        qa_label = QLabel("图文问答:")
        text_layout.addWidget(qa_label)
        
        self.qa_scroll = QScrollArea()
        self.qa_container = QWidget()
        self.qa_container_layout = QVBoxLayout(self.qa_container)
        self.qa_container_layout.setAlignment(Qt.AlignTop)
        self.qa_scroll.setWidget(self.qa_container)
        self.qa_scroll.setWidgetResizable(True)
        text_layout.addWidget(self.qa_scroll, 3)
        
        # 问答来源标签
        self.qa_source_label = QLabel("问答来源: 尚未加载")
        text_layout.addWidget(self.qa_source_label)
        
        main_display.addWidget(text_frame)
        
        layout.addWidget(main_display, 1)
        
        # 控制区域
        control_group = QGroupBox("数据校正控制")
        control_layout = QVBoxLayout()
        
        # 进度条（单独一行）
        progress_layout = QHBoxLayout()
        self.progress_label = QLabel("0/0")
        self.progress_label.setFixedWidth(80)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setFormat("%p% (%v/%m)")
        
        progress_layout.addWidget(self.progress_label)
        progress_layout.addWidget(self.progress_bar)
        control_layout.addLayout(progress_layout)
        
        # 导航按钮
        nav_layout = QHBoxLayout()
        self.prev_button = QPushButton("上一张 (←/↑)")
        nav_layout.addWidget(self.prev_button)
        
        self.next_button = QPushButton("下一张 (→/↓)")
        nav_layout.addWidget(self.next_button)
        control_layout.addLayout(nav_layout)
        
        # 操作按钮
        action_layout = QHBoxLayout()
        self.add_caption_btn = QPushButton("添加图像描述")
        action_layout.addWidget(self.add_caption_btn)
        
        self.add_vqa_btn = QPushButton("添加视觉问答对")
        action_layout.addWidget(self.add_vqa_btn)
        
        self.save_btn = QPushButton("保存标注 (Ctrl+S)")
        action_layout.addWidget(self.save_btn)
        control_layout.addLayout(action_layout)
        
        # 检测框按钮
        bbox_layout = QHBoxLayout()
        self.show_bbox_btn = QPushButton("显示检测框")
        bbox_layout.addWidget(self.show_bbox_btn)
        
        self.hide_bbox_btn = QPushButton("隐藏检测框")
        bbox_layout.addWidget(self.hide_bbox_btn)
        control_layout.addLayout(bbox_layout)
        
        control_group.setLayout(control_layout)
        layout.addWidget(control_group)
        
        self.setLayout(layout)
        
        # 显示示例图像
        self.show_example_image()
    
    def show_example_image(self):
        # 创建示例图像
        pixmap = QPixmap(600, 400)
        pixmap.fill(QColor(30, 30, 50))
        
        painter = QPainter(pixmap)
        painter.setPen(QColor(100, 180, 255))
        painter.setFont(QFont("Arial", 24))
        painter.drawText(pixmap.rect(), Qt.AlignCenter, "图像预览区域")
        painter.end()
        
        self.image_label.setPixmap(pixmap)
        
        # 设置示例文本
        self.desc_text.setPlainText("图像描述示例：机场鸟瞰图，包含多架商业客机停放在停机坪上，远处有控制塔和候机楼。")
        
        # 添加示例问答
        self.add_qa_row("问：图像中有多少架飞机？", "答：图像中可见12架飞机停放在停机坪上。")
        self.add_qa_row("问：机场的主要设施有哪些？", "答：机场包含控制塔、候机楼、跑道和多个停机位。")
    
    def add_qa_row(self, question="", answer=""):
        """添加一个问答对行"""
        qa_frame = QFrame()
        qa_frame.setFrameShape(QFrame.StyledPanel)
        qa_frame.setStyleSheet("background-color: rgba(40, 40, 60, 150); border-radius: 6px;")
        qa_layout = QVBoxLayout(qa_frame)
        qa_layout.setContentsMargins(10, 10, 10, 10)
        
        # 问题标签
        q_label = QLabel("问题:")
        qa_layout.addWidget(q_label)
        
        # 问题文本框
        question_txt = QTextEdit()
        question_txt.setPlainText(question)
        question_txt.setMinimumHeight(50)
        qa_layout.addWidget(question_txt)
        
        # 答案标签
        a_label = QLabel("答案:")
        qa_layout.addWidget(a_label)
        
        # 答案文本框
        answer_txt = QTextEdit()
        answer_txt.setPlainText(answer)
        answer_txt.setMinimumHeight(80)
        qa_layout.addWidget(answer_txt)
        
        # 删除按钮
        btn_delete = QPushButton("删除此问答对")
        btn_delete.setStyleSheet("background-color: rgba(180, 80, 80, 150);")
        btn_delete.clicked.connect(lambda: self.delete_qa_row(qa_frame))
        qa_layout.addWidget(btn_delete)
        
        # 添加到容器
        self.qa_container_layout.addWidget(qa_frame)
    
    def delete_qa_row(self, frame):
        """删除特定的问答对行"""
        frame.deleteLater()
    
    def select_img_path(self):
        path = QFileDialog.getExistingDirectory(self, "选择图像文件夹")
        if path:
            self.img_path_edit.setText(path)
    
    def select_ann_path(self):
        path = QFileDialog.getExistingDirectory(self, "选择标注文件夹")
        if path:
            self.ann_path_edit.setText(path)
    
    def select_json_path(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "选择JSON文件", "", "JSON文件 (*.json)")
        if file_path:
            self.json_path_edit.setText(file_path)

# ========================================================
# 主程序入口
# ========================================================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # 设置应用字体
    font = QFont("Noto Sans SC")
    app.setFont(font)
    
    # 设置应用样式
    app.setStyle("Fusion")
    
    # 创建主窗口
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec_())
