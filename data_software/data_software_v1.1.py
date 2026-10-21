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
    QListWidgetItem, QStatusBar, QSizeGrip, QGraphicsOpacityEffect, QFileDialog
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
                background-color: rgba(20, 20, 35, 200);
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

        # Logo和标题
        self.logo = QLabel()
        self.logo.setPixmap(QPixmap("CASC-LOGO-transparency.png").scaled(30, 30, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        layout.addWidget(self.logo)
        
        self.title = QLabel("多模态大模型训练数据管理平台")
        self.title.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: #8ab4f8;
            background: transparent;
        """)
        layout.addWidget(self.title)
        
        # 添加动画效果 - 使用图形效果代替属性动画
        self.title_effect = QGraphicsOpacityEffect(self.title)
        self.title_effect.setOpacity(1.0)  # 设置初始透明度
        self.title.setGraphicsEffect(self.title_effect)
        
        self.title_animation = QPropertyAnimation(self.title_effect, b"opacity")
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
        self.setWindowIcon(QIcon("CASC-LOGO-transparency.png"))
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
        
        # 添加帮助按钮
        self.btn_help = SidebarButton("icons/help.png", "帮助")
        self.btn_help.clicked.connect(lambda: self.switch_page(3))
        
        sidebar_layout.addWidget(self.btn_data_select)
        sidebar_layout.addWidget(self.btn_data_cap_vqa)
        sidebar_layout.addWidget(self.btn_data_refine)
        sidebar_layout.addWidget(self.btn_help)
        
        sidebar_layout.addStretch()
        
        # 添加版本信息
        version = QLabel("v1.1")
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
        
        # 添加四个功能页面
        self.data_select_widget = DataSelectWidget()
        self.data_cap_vqa_widget = DataCapVqaWidget()
        self.data_refine_widget = DataRefineWidget()
        self.help_widget = HelpWidget()  # 添加帮助页面
        
        self.stacked_widget.addWidget(self.data_select_widget)
        self.stacked_widget.addWidget(self.data_cap_vqa_widget)
        self.stacked_widget.addWidget(self.data_refine_widget)
        self.stacked_widget.addWidget(self.help_widget)
        
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
        self.btn_help.setChecked(index == 3)
        
        # 更新状态栏
        pages = ["图像数据筛选", "视觉-语言任务衍生数据生成", "视觉-语言任务衍生数据校正", "帮助"]
        self.status_label.setText(f"当前页面: {pages[index]}")


# ========================================================
# 多进程处理工作线程
# ========================================================
class SearchWorker(QThread):
    """后台工作线程，用于在搜索时处理JSON文件"""
    search_finished = pyqtSignal(list, str)  # 搜索完成信号
    progress_updated = pyqtSignal(int, int)  # 进度更新信号
    error_occurred = pyqtSignal(str)  # 错误信号
    
    def __init__(self, labels_path, search_term):
        super().__init__()
        self.labels_path = labels_path
        self.search_term = search_term
        self.running = True
    
    def run(self):
        """线程主执行函数"""
        try:
            if not os.path.exists(self.labels_path):
                self.error_occurred.emit(f"目录 {self.labels_path} 不存在！")
                return
                
            search_results = []
            json_files = [f for f in os.listdir(self.labels_path) if f.endswith(".json")]
            total_files = len(json_files)
            
            for idx, filename in enumerate(json_files):
                if not self.running:  # 检查是否已请求停止
                    return
                    
                filepath = os.path.join(self.labels_path, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        # 检查annotations中是否包含搜索词
                        if self.contains_search_term(data, self.search_term):
                            search_results.append(filename.replace(".json", ""))
                except Exception as e:
                    self.error_occurred.emit(f"读取文件 {filename} 出错: {str(e)}")
                    continue
                
                # 每处理5个文件更新一次进度，减少UI更新频率
                if idx % 5 == 0:
                    self.progress_updated.emit(idx + 1, total_files)
            
            # 确保最后100%更新
            self.progress_updated.emit(total_files, total_files)
            self.search_finished.emit(search_results, self.search_term)
            
        except Exception as e:
            self.error_occurred.emit(f"搜索过程中发生错误: {str(e)}")
    
    def contains_search_term(self, data, search_term):
        """检查JSON数据中是否包含搜索词（修改：空搜索词返回所有文件）"""
        # 如果搜索词为空，返回所有文件
        if not search_term.strip():
            return True
            
        if "annotations" in data:
            for annotation in data["annotations"]:
                if ("class" in annotation and search_term in annotation["class"]) or \
                   ("label" in annotation and search_term in annotation["label"]):
                    return True
        return False
    
    def stop(self):
        """请求停止线程"""
        self.running = False


# ========================================================
# 图像数据筛选模块 (基于data_select.py)
# ========================================================
class DataSelectWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.search_worker = None  # 搜索工作线程
        self.search_results = []   # 搜索结果列表
        self.current_index = -1    # 当前显示索引
        self.current_basename = "" # 当前图像的基本名
        self.current_image_path = "" # 当前图像路径
        self.saved_count = 0       # 已保存图像计数
        self.images_path = ""      # 图像路径
        self.labels_path = ""      # 标签路径
        self.show_bbox = False    # 是否显示检测框
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
    
    def create_data_config_group(self):
        # 数据配置卡片
        config_group = QGroupBox("数据配置")
        config_layout = QVBoxLayout()
        
        # 图像数据集目录
        img_layout = QHBoxLayout()
        img_layout.addWidget(QLabel("图像数据集目录:"))
        self.images_path_label = QLabel("未选择")
        img_layout.addWidget(self.images_path_label, 1)
        
        img_btn = QPushButton("浏览")
        img_btn.clicked.connect(self.select_images_path)
        img_layout.addWidget(img_btn)
        config_layout.addLayout(img_layout)
        
        # 标签数据集目录
        label_layout = QHBoxLayout()
        label_layout.addWidget(QLabel("标签数据集目录:"))
        self.labels_path_label = QLabel("未选择")
        label_layout.addWidget(self.labels_path_label, 1)
        
        label_btn = QPushButton("浏览")
        label_btn.clicked.connect(self.select_labels_path)
        label_layout.addWidget(label_btn)
        config_layout.addLayout(label_layout)
        
        # 视觉衍生文本数据集文件（可选）
        text_layout = QHBoxLayout()
        text_layout.addWidget(QLabel("视觉衍生文本数据集文件（可选）:"))
        self.text_path_label = QLabel("未选择")
        text_layout.addWidget(self.text_path_label, 1)
        
        text_btn = QPushButton("浏览")
        text_btn.clicked.connect(self.select_text_path)
        text_layout.addWidget(text_btn)
        config_layout.addLayout(text_layout)
        
        config_group.setLayout(config_layout)
        return config_group
    
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # 标题
        title = QLabel("图像数据（已标&未标）高质量筛选")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #8ab4f8;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # 添加数据配置卡片
        config_group = self.create_data_config_group()
        layout.addWidget(config_group)
        
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
        
        # 创建滚动区域确保大图像可以查看
        image_scroll = QScrollArea()
        image_scroll.setWidget(self.image_display)
        image_scroll.setWidgetResizable(True)
        
        self.image_filename_label = QLabel("图像文件名: ")
        self.image_filename_label.setAlignment(Qt.AlignCenter)
        
        image_layout.addWidget(image_scroll, 3)
        image_layout.addWidget(self.image_filename_label, 1)
        image_group.setLayout(image_layout)
        
        # JSON预览
        json_group = QGroupBox("标签详情")
        json_layout = QVBoxLayout()
        
        self.json_display = QTextEdit()
        self.json_display.setReadOnly(True)
        self.json_display.setFont(QFont("Noto Sans SC", 10))  # 设置支持中文的字体
        
        # 创建滚动区域确保长文本可以查看
        json_scroll = QScrollArea()
        json_scroll.setWidget(self.json_display)
        json_scroll.setWidgetResizable(True)
        
        self.json_filename_label = QLabel("标签文件名: ")
        self.json_filename_label.setAlignment(Qt.AlignCenter)
        
        json_layout.addWidget(json_scroll, 3)
        json_layout.addWidget(self.json_filename_label, 1)
        json_group.setLayout(json_layout)
        
        display_layout.addWidget(image_group, 1)
        display_layout.addWidget(json_group, 1)
        display_group.setLayout(display_layout)
        layout.addWidget(display_group, 1)
        
        # 控制区域
        control_group = QGroupBox("数据操作")
        control_layout = QVBoxLayout()
        
        # 第一行：进度条和已保存计数
        progress_layout = QHBoxLayout()
        
        # 进度条部分
        progress_bar_layout = QHBoxLayout()
        # self.progress_label = QLabel("0/0")
        # self.progress_label.setFixedWidth(80)
        self.progress_bar = QProgressBar()
        self.progress_bar.setFormat("%p% (%v/%m)")
        progress_bar_layout.addWidget(self.progress_label)
        progress_bar_layout.addWidget(self.progress_bar)
        
        progress_layout.addLayout(progress_bar_layout, 4)  # 占4份空间
        
        # 已保存计数部分
        saved_count_frame = QFrame()
        saved_count_layout = QVBoxLayout(saved_count_frame)
        saved_count_layout.setContentsMargins(10, 5, 10, 5)
        saved_count_layout.setAlignment(Qt.AlignCenter)
        
        saved_label = QLabel("已保存图像")
        saved_label.setAlignment(Qt.AlignCenter)
        saved_label.setStyleSheet("font-size: 14px; color: #a0a0e0;")
        
        self.saved_count_display = QLabel("0")
        self.saved_count_display.setAlignment(Qt.AlignCenter)
        self.saved_count_display.setFont(QFont("Arial", 16, QFont.Bold))
        self.saved_count_display.setStyleSheet("color: #8ab4f8;")
        
        saved_count_layout.addWidget(saved_label)
        saved_count_layout.addWidget(self.saved_count_display)
        
        progress_layout.addWidget(saved_count_frame, 1)  # 占1份空间
        
        control_layout.addLayout(progress_layout)
        
        # 第二行：导航按钮（填满整行）
        nav_layout = QHBoxLayout()
        
        # 上一张按钮（左侧）
        self.prev_button = QPushButton("上一张 (←/↑)")
        self.prev_button.setEnabled(False)
        self.prev_button.clicked.connect(self.show_prev_image)
        self.prev_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)  # 可扩展
        nav_layout.addWidget(self.prev_button, 1)  # 占1份空间
        
        # 下一张按钮（右侧）
        self.next_button = QPushButton("下一张 (→/↓)")
        self.next_button.setEnabled(False)
        self.next_button.clicked.connect(self.show_next_image)
        self.next_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)  # 可扩展
        nav_layout.addWidget(self.next_button, 1)  # 占1份空间
        
        control_layout.addLayout(nav_layout)
        
        # 第三行：操作按钮
        action_layout = QHBoxLayout()
        
        # 保存按钮（左侧）
        self.save_button = QPushButton("保存当前图像 (Ctrl+S)")
        self.save_button.setEnabled(False)
        self.save_button.clicked.connect(self.save_current_image)
        self.save_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)  # 可扩展
        action_layout.addWidget(self.save_button, 1)  # 占1份空间
        
        # 剔除按钮（右侧）
        self.discard_button = QPushButton("不保存并剔除 (Del/Backs)")
        self.discard_button.setEnabled(False)
        self.discard_button.clicked.connect(self.discard_current_image)
        self.discard_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)  # 可扩展
        action_layout.addWidget(self.discard_button, 1)  # 占1份空间
        
        control_layout.addLayout(action_layout)
        
        # 第四行：检测框按钮
        bbox_layout = QHBoxLayout()
        
        # 显示检测框按钮（左侧）
        self.show_bbox_button = QPushButton("显示检测框")
        self.show_bbox_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)  # 可扩展
        bbox_layout.addWidget(self.show_bbox_button, 1)  # 占1份空间
        
        # 隐藏检测框按钮（右侧）
        self.hide_bbox_button = QPushButton("隐藏检测框")
        self.hide_bbox_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)  # 可扩展
        bbox_layout.addWidget(self.hide_bbox_button, 1)  # 占1份空间
        
        control_layout.addLayout(bbox_layout)
        
        control_group.setLayout(control_layout)
        layout.addWidget(control_group)
        
        self.setLayout(layout)
    
    def select_images_path(self):
        path = QFileDialog.getExistingDirectory(self, "选择图像文件夹")
        if path:
            self.images_path_label.setText(path)
            self.images_path = path
    
    def select_labels_path(self):
        path = QFileDialog.getExistingDirectory(self, "选择标签文件夹")
        if path:
            self.labels_path_label.setText(path)
            self.labels_path = path
    
    def select_text_path(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "选择文本数据集文件", "", "文本文件 (*.txt *.json)")
        if file_path:
            self.text_path_label.setText(file_path)
    
    def start_search(self):
        # 获取搜索关键词
        search_term = self.search_input.text().strip()
        
        # 检查标签路径是否设置
        labels_path = self.labels_path_label.text()
        if labels_path == "未选择":
            QMessageBox.warning(self, "路径未设置", "请先选择标签数据集目录！")
            return
        
        # 检查图像路径是否设置
        images_path = self.images_path_label.text()
        if images_path == "未选择":
            QMessageBox.warning(self, "路径未设置", "请先选择图像数据集目录！")
            return
        
        # 重置状态
        self.search_results = []
        self.current_index = -1
        self.prev_button.setEnabled(False)
        self.next_button.setEnabled(False)
        self.save_button.setEnabled(False)
        self.discard_button.setEnabled(False)
        self.progress_bar.setValue(0)
        self.progress_bar.setMaximum(0)  # 重置最大值
        
        # 显示搜索状态
        self.progress_label.setText("搜索中...")
        self.json_display.setPlainText("正在搜索...")
        
        # 创建并启动搜索工作线程
        if self.search_worker:
            self.search_worker.stop()
        
        self.search_worker = SearchWorker(labels_path, search_term)
        self.search_worker.search_finished.connect(self.handle_search_results)
        self.search_worker.progress_updated.connect(self.update_search_progress)
        self.search_worker.error_occurred.connect(self.handle_search_error)
        self.search_worker.start()
    
    def update_search_progress(self, current, total):
        """更新搜索进度"""
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(current)
        self.progress_label.setText(f"{current}/{total}")
    
    def handle_search_results(self, results, search_term):
        """处理搜索结果"""
        self.search_results = results
        total = len(results)
        
        if total == 0:
            self.progress_label.setText("0/0")
            self.json_display.setPlainText(f"未找到包含 '{search_term}' 的结果")
            QMessageBox.information(self, "搜索完成", f"未找到包含 '{search_term}' 的结果")
            return
        
        # 设置进度条最大值为搜索结果总数
        self.progress_bar.setMaximum(total)
        
        # 显示第一个结果
        self.current_index = 0
        self.show_current_result()
        
        # 更新按钮状态
        self.prev_button.setEnabled(total > 1)
        self.next_button.setEnabled(total > 1)
        self.save_button.setEnabled(True)
        self.discard_button.setEnabled(True)
        
        # 更新状态
        self.progress_label.setText(f"1/{total}")
        self.progress_bar.setValue(1)
        QMessageBox.information(self, "搜索完成", f"找到 {total} 个匹配结果")
    
    def handle_search_error(self, error_msg):
        """处理搜索错误"""
        QMessageBox.critical(self, "搜索错误", error_msg)
        self.progress_label.setText("错误")
        self.json_display.setPlainText(error_msg)
    
    def draw_bounding_boxes(self, image, basename):
        """绘制仅包含搜索关键词的检测框"""
        json_path = os.path.join(self.labels_path, f"{basename}.json")
        if not os.path.exists(json_path):
            return image
            
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
                
            # 将QImage转换为QPixmap以便使用QPainter
            pixmap = QPixmap.fromImage(image)
            painter = QPainter(pixmap)
            pen = QPen(QColor(255, 0, 0), 2)  # 红色，2像素宽
            painter.setPen(pen)
            
            # 只绘制包含搜索关键词的检测框
            if "annotations" in json_data:
                for annotation in json_data["annotations"]:
                    # 检查标注是否包含搜索关键词
                    if "coordinates of the corner point(Col,Row)" in annotation:
                        search_term = self.search_input.text().strip()
                        if not search_term:  # 如果搜索词为空，绘制所有检测框
                            should_draw = True
                        else:
                            should_draw = ("class" in annotation and search_term in annotation["class"]) or \
                                         ("label" in annotation and search_term in annotation["label"])
                        
                        if should_draw:
                            points = []
                            for coord in annotation["coordinates of the corner point(Col,Row)"]:
                                col, row = map(int, coord.split(','))
                                points.append(QPoint(col, row))
                            
                            # 绘制多边形
                            for i in range(len(points)):
                                painter.drawLine(points[i], points[(i+1)%len(points)])
                            
                            # 标注类别和ID
                            if "class" in annotation and "label" in annotation and "id" in annotation:
                                label = f"{annotation['class']} {annotation['label']} {annotation['id']}"
                                painter.drawText(points[0], label)
            
            painter.end()
            return pixmap.toImage()  # 转换回QImage
            
        except Exception as e:
            print(f"绘制检测框出错: {str(e)}")
            return image
    
    def toggle_bbox_display(self):
        """切换检测框显示状态"""
        sender = self.sender()
        if sender == self.show_bbox_button:
            self.show_bbox = True
        else:
            self.show_bbox = False
        self.show_current_result()  # 刷新显示
    
    def show_current_result(self):
        """显示当前索引的图像和标签"""
        if not self.search_results or self.current_index < 0 or self.current_index >= len(self.search_results):
            return
        
        # 更新进度显示
        current_progress = self.current_index + 1
        total = len(self.search_results)
        self.progress_label.setText(f"{current_progress}/{total}")
        self.progress_bar.setValue(current_progress)
        
        basename = self.search_results[self.current_index]
        self.current_basename = basename
        
        # 显示图像文件名
        self.image_filename = ""
        found_ext = ""
        
        # 显示图像
        image_found = False
        image_path = ""
        
        if self.images_path:
            # 尝试常见图像格式
            for ext in ['.jpg', '.png', '.tif', '.tiff', '.bmp', '.jpeg', '.JPG', '.PNG']:
                test_path = os.path.join(self.images_path, f"{basename}{ext}")
                if os.path.exists(test_path):
                    image_found = True
                    image_path = test_path
                    self.image_filename = f"{basename}{ext}"
                    found_ext = ext
                    self.current_image_path = image_path
                    break
        
        if image_found:
            # 使用QImage加载图像
            image = QImage(image_path)
            if not image.isNull():
                # 如果开启显示检测框，则绘制检测框
                if self.show_bbox:
                    image = self.draw_bounding_boxes(image, basename)
                
                # 将QImage转换为QPixmap用于显示
                pixmap = QPixmap.fromImage(image)
                
                # 调整图像大小以适应显示区域
                scaled_pixmap = pixmap.scaled(
                    self.image_display.width(),
                    self.image_display.height(),
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
                self.image_display.setPixmap(scaled_pixmap)
                self.image_display.setScaledContents(False)  # 确保图像不会拉伸
                self.image_filename_label.setText(f"图像文件名: {self.image_filename}")
            else:
                self.image_display.setText("无法加载图像")
                self.image_filename_label.setText(f"图像加载失败: {self.image_filename}")
        else:
            if self.images_path:
                self.image_display.setText(f"图像文件不存在: {basename}.*")
                self.image_filename_label.setText(f"图像文件: {basename} 未找到")
            else:
                self.image_display.setText("请先选择图像文件夹")
                self.image_filename_label.setText("图像路径未设置")
        
        # 显示JSON内容
        json_path = os.path.join(self.labels_path, f"{basename}.json")
        json_filename = f"{basename}.json"
        self.json_filename_label.setText(f"标签文件名: {json_filename}")
        
        if os.path.exists(json_path):
            try:
                with open(json_path, 'r', encoding='utf-8') as f:
                    json_data = json.load(f)
                    # 使用ensure_ascii=False确保中文正常显示
                    formatted_json = json.dumps(json_data, ensure_ascii=False, indent=2)
                    self.json_display.setPlainText(formatted_json)
            except Exception as e:
                self.json_display.setPlainText(f"读取JSON文件出错:\n{str(e)}")
        else:
            self.json_display.setPlainText(f"JSON文件不存在: {json_path}")
    
    def show_prev_image(self):
        """显示上一张图像"""
        if self.current_index > 0:
            self.current_index -= 1
            self.show_current_result()
    
    def show_next_image(self):
        """显示下一张图像"""
        if self.current_index < len(self.search_results) - 1:
            self.current_index += 1
            self.show_current_result()
    
    def save_current_image(self):
        """保存当前图像"""
        if not self.search_results or self.current_index < 0:
            return
        
        # 更新保存计数
        self.saved_count += 1
        self.saved_count_display.setText(str(self.saved_count))
        
        # 显示保存成功的消息
        QMessageBox.information(self, "保存成功", f"已保存当前图像 ({self.saved_count})")
    
    def discard_current_image(self):
        """不保存并剔除当前图像"""
        if not self.search_results or self.current_index < 0:
            return
        
        # 从搜索结果中移除当前图像
        self.search_results.pop(self.current_index)
        total = len(self.search_results)
        
        # 更新进度条最大值
        self.progress_bar.setMaximum(total)
        
        # 更新显示
        if total == 0:
            # 没有更多图像
            self.current_index = -1
            self.image_display.clear()
            self.json_display.clear()
            self.image_filename_label.setText("图像文件名: ")
            self.json_filename_label.setText("标签文件名: ")
            self.prev_button.setEnabled(False)
            self.next_button.setEnabled(False)
            self.save_button.setEnabled(False)
            self.discard_button.setEnabled(False)
            self.progress_label.setText("0/0")
            self.progress_bar.setValue(0)
            QMessageBox.information(self, "完成", "已剔除所有图像")
        elif self.current_index >= total:
            # 如果剔除的是最后一个，显示前一个
            self.current_index = total - 1
            self.show_current_result()
        else:
            # 显示当前索引（剔除后索引不变，但内容已更新）
            self.show_current_result()


# ========================================================
# 视觉-语言任务衍生数据生成模块 (基于data_cap_vqa.py)
# ========================================================
class DataCapVqaWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.setup_style()
    
    def create_data_config_group(self):
        # 数据配置卡片
        config_group = QGroupBox("数据配置")
        config_layout = QVBoxLayout()
        
        # 图像数据集目录
        img_layout = QHBoxLayout()
        img_layout.addWidget(QLabel("图像数据集目录:"))
        self.img_path_label = QLabel("未选择")
        img_layout.addWidget(self.img_path_label, 1)
        
        img_btn = QPushButton("浏览")
        img_btn.clicked.connect(self.select_img_path)
        img_layout.addWidget(img_btn)
        config_layout.addLayout(img_layout)
        
        # 标签数据集目录
        label_layout = QHBoxLayout()
        label_layout.addWidget(QLabel("标签数据集目录:"))
        self.label_path_label = QLabel("未选择")
        label_layout.addWidget(self.label_path_label, 1)
        
        label_btn = QPushButton("浏览")
        label_btn.clicked.connect(self.select_label_path)
        label_layout.addWidget(label_btn)
        config_layout.addLayout(label_layout)
        
        # 视觉衍生文本数据集文件（可选）
        text_layout = QHBoxLayout()
        text_layout.addWidget(QLabel("视觉衍生文本数据集文件（可选）:"))
        self.text_path_label = QLabel("未选择")
        text_layout.addWidget(self.text_path_label, 1)
        
        text_btn = QPushButton("浏览")
        text_btn.clicked.connect(self.select_text_path)
        text_layout.addWidget(text_btn)
        config_layout.addLayout(text_layout)
        
        config_group.setLayout(config_layout)
        return config_group
    
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
        
        # 添加数据配置卡片
        config_group = self.create_data_config_group()
        layout.addWidget(config_group)
        
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
        
        # 输出文件夹
        output_layout = QHBoxLayout()
        output_layout.addWidget(QLabel("输出文件夹:"))
        self.output_path_edit = QLineEdit()
        output_layout.addWidget(self.output_path_edit, 3)
        
        output_btn = QPushButton("浏览")
        output_btn.clicked.connect(self.select_output_path)
        output_layout.addWidget(output_btn, 1)
        layout.addLayout(output_layout)
        
        # 处理参数
        param_layout = QHBoxLayout()
        param_layout.addWidget(QLabel("分块大小:"))
        self.chunk_size_edit = QLineEdit("1024")
        param_layout.addWidget(self.chunk_size_edit)
        
        param_layout.addWidget(QLabel("分块数量:"))
        self.chunk_num_edit = QLineEdit("5")
        param_layout.addWidget(self.chunk_num_edit)
        
        param_layout.addStretch()
        layout.addLayout(param_layout)
        
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
            self.img_path_label.setText(path)
    
    def select_label_path(self):
        path = QFileDialog.getExistingDirectory(self, "选择标签文件夹")
        if path:
            self.label_path_label.setText(path)
    
    def select_text_path(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "选择文本数据集文件", "", "文本文件 (*.txt *.json)")
        if file_path:
            self.text_path_label.setText(file_path)
    
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
    
    def create_data_config_group(self):
        # 数据配置卡片
        config_group = QGroupBox("数据配置")
        config_layout = QVBoxLayout()
        
        # 图像数据集目录
        img_layout = QHBoxLayout()
        img_layout.addWidget(QLabel("图像数据集目录:"))
        self.img_path_label = QLabel("未选择")
        img_layout.addWidget(self.img_path_label, 1)
        
        img_btn = QPushButton("浏览")
        img_btn.clicked.connect(self.select_img_path)
        img_layout.addWidget(img_btn)
        config_layout.addLayout(img_layout)
        
        # 标签数据集目录
        label_layout = QHBoxLayout()
        label_layout.addWidget(QLabel("标签数据集目录:"))
        self.label_path_label = QLabel("未选择")
        label_layout.addWidget(self.label_path_label, 1)
        
        label_btn = QPushButton("浏览")
        label_btn.clicked.connect(self.select_label_path)
        label_layout.addWidget(label_btn)
        config_layout.addLayout(label_layout)
        
        # 视觉衍生文本数据集文件（可选）
        text_layout = QHBoxLayout()
        text_layout.addWidget(QLabel("视觉衍生文本数据集文件（可选）:"))
        self.text_path_label = QLabel("未选择")
        text_layout.addWidget(self.text_path_label, 1)
        
        text_btn = QPushButton("浏览")
        text_btn.clicked.connect(self.select_text_path)
        text_layout.addWidget(text_btn)
        config_layout.addLayout(text_layout)
        
        config_group.setLayout(config_layout)
        return config_group
    
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
        
        # 添加数据配置卡片
        config_group = self.create_data_config_group()
        layout.addWidget(config_group)
        
        # 数据预览卡片（仿照第一个功能界面）
        display_group = QGroupBox("数据预览")
        display_layout = QHBoxLayout()
        
        # 左侧图像面板
        image_group = QGroupBox("图像预览")
        image_layout = QVBoxLayout()
        
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
        
        image_group.setLayout(image_layout)
        
        # 右侧文本面板
        text_group = QGroupBox("文本预览")
        text_layout = QVBoxLayout()
        
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
        
        text_group.setLayout(text_layout)
        
        display_layout.addWidget(image_group, 1)
        display_layout.addWidget(text_group, 1)
        display_group.setLayout(display_layout)
        layout.addWidget(display_group, 1)
        
        # 控制区域
        control_group = QGroupBox("数据校正控制操作")
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
            self.img_path_label.setText(path)
    
    def select_label_path(self):
        path = QFileDialog.getExistingDirectory(self, "选择标签文件夹")
        if path:
            self.label_path_label.setText(path)
    
    def select_text_path(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "选择文本数据集文件", "", "文本文件 (*.txt *.json)")
        if file_path:
            self.text_path_label.setText(file_path)


# ========================================================
# 帮助页面
# ========================================================
class HelpWidget(QWidget):
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
            QTextEdit {
                background-color: rgba(25, 25, 40, 200);
                color: #e0e0ff;
                border: 1px solid #444466;
                border-radius: 4px;
                padding: 5px;
            }
        """)
    
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # 标题
        title = QLabel("帮助中心")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #8ab4f8;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # 使用说明
        usage_group = QGroupBox("使用说明")
        usage_layout = QVBoxLayout()
        
        usage_text = QTextEdit()
        usage_text.setReadOnly(True)
        usage_text.setHtml("""
            <h3>多模态大模型训练数据管理平台功能说明</h3>
            <p><b>1. 图像数据筛选</b></p>
            <p>用于筛选已标注和未标注的图像数据：</p>
            <ul>
                <li>设置图像数据集目录和标签数据集目录</li>
                <li>输入关键词筛选相关图像</li>
                <li>预览图像和标签详情</li>
                <li>支持算法去重功能（开发中）</li>
            </ul>
            
            <p><b>2. 视觉-语言任务衍生数据生成</b></p>
            <p>用于生成图像描述和视觉问答对：</p>
            <ul>
                <li>配置模型参数和API设置</li>
                <li>设置输入图像路径和输出目录</li>
                <li>自定义提示词模板</li>
                <li>批量生成图像描述和问答对</li>
            </ul>
            
            <p><b>3. 视觉-语言任务衍生数据校正</b></p>
            <p>用于校正生成的描述和问答对：</p>
            <ul>
                <li>加载图像、标签和文本数据集</li>
                <li>预览图像及相关文本描述</li>
                <li>编辑和修正描述及问答内容</li>
                <li>添加新的描述和问答对</li>
            </ul>
        """)
        usage_layout.addWidget(usage_text)
        usage_group.setLayout(usage_layout)
        layout.addWidget(usage_group, 1)
        
        # 关于信息
        about_group = QGroupBox("关于")
        about_layout = QVBoxLayout()
        
        about_text = QTextEdit()
        about_text.setReadOnly(True)
        about_text.setHtml("""
            <h3>多模态大模型训练数据管理平台</h3>
            <p><b>版本：</b> v1.1</p>
            <p><b>功能：</b> 提供图像数据筛选、视觉-语言任务衍生数据生成与校正功能</p>
            <p><b>作者：</b> LX</p>
            <p><b>开发时间：</b> 2025年07月</p>
            <p><b>技术支持：</b> 智能前沿所</p>
            <p><b>版权声明：</b> © 2025 智能前沿所 保留所有权利</p>
        """)
        about_layout.addWidget(about_text)
        about_group.setLayout(about_layout)
        layout.addWidget(about_group)
        
        self.setLayout(layout)


# ========================================================
# 主程序入口
# ========================================================
# 在创建 QApplication 之后，但在创建主窗口之前设置文件对话框样式
if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # 设置文件对话框的样式
    app.setStyleSheet("""
        QFileDialog {
            background-color: #2a2a4a;
            color: #e0e0ff;
        }
        QFileDialog QLabel {
            color: #c0c0e0;
        }
        QFileDialog QListView, QFileDialog QTreeView {
            background-color: #1a1a2a;
            color: #e0e0ff;
            alternate-background-color: #252545;
        }
        QFileDialog QHeaderView::section {
            background-color: #2a2a4a;
            color: #e0e0ff;
            border: 1px solid #444466;
        }
        QFileDialog QPushButton {
            background-color: rgba(60, 60, 100, 200);
            color: #e0e0ff;
            border: 1px solid #4a4a7a;
            border-radius: 4px;
            padding: 5px 10px;
        }
        QFileDialog QPushButton:hover {
            background-color: rgba(80, 80, 130, 220);
            border: 1px solid #6a6aaa;
        }
        QFileDialog QLineEdit {
            background-color: rgba(25, 25, 40, 200);
            color: #e0e0ff;
            border: 1px solid #444466;
            border-radius: 4px;
            padding: 5px;
        }
    """)
    
    # 设置应用字体
    font = QFont("Noto Sans SC")
    app.setFont(font)
    
    # 设置应用样式
    app.setStyle("Fusion")
    
    # 创建主窗口
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec_())
