import sys
import os
import json
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QStackedWidget,
                             QFrame, QSplitter, QSizePolicy, QDialog, QLineEdit,
                             QTextEdit, QMenu, QComboBox, QGroupBox, QFileDialog)
from PyQt5.QtCore import Qt, QSize, QTimer
from PyQt5.QtGui import QFont, QIcon, QColor, QPalette, QPixmap, QPainter

# 忽略TIFF库的特定警告 (解决TIFFReadDirectory警告问题)
os.environ['OPENCV_IO_IGNORE_TIFF_WARNINGS'] = '1'

class TechButton(QPushButton):
    """自定义技术风格按钮"""
    def __init__(self, text, icon=None):
        super().__init__(text)
        self.setMinimumHeight(50)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        font = QFont("Segoe UI", 9, QFont.Bold)
        self.setFont(font)
        self.normal_style = """
            QPushButton {
                background-color: #e6f7ff;
                color: #0066cc;
                border: 1px solid #66b3ff;
                border-radius: 8px;
                text-align: center;
                padding: 5px;
                margin: 2px;
            }
            QPushButton:hover {
                background-color: #d1e8ff;
                border: 1px solid #3399ff;
            }
            QPushButton:pressed {
                background-color: #b3d9ff;
            }
        """
        self.active_style = """
            QPushButton {
                background-color: #cce6ff;
                color: #004d99;
                border: 1px solid #3399ff;
                border-radius: 8px;
                text-align: center;
                padding: 5px;
                margin: 2px;
            }
        """
        self.setStyleSheet(self.normal_style)
        if icon:
            self.setIcon(QIcon(icon))
            self.setIconSize(QSize(20, 20))

class SettingsDialog(QDialog):
    """设置对话框，包含API、模型和图标配置"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("设置")
        self.resize(600, 500)  # 放大窗口尺寸
        
        main_layout = QVBoxLayout()
        
        # API设置组
        api_group = QGroupBox("API设置")
        api_layout = QVBoxLayout(api_group)
        
        url_layout = QHBoxLayout()
        url_layout.addWidget(QLabel("API_URL:"))
        self.url_edit = QLineEdit()
        url_layout.addWidget(self.url_edit)
        api_layout.addLayout(url_layout)
        
        key_layout = QHBoxLayout()
        key_layout.addWidget(QLabel("API_KEY:"))
        self.key_edit = QLineEdit()
        key_layout.addWidget(self.key_edit)
        api_layout.addLayout(key_layout)
        
        main_layout.addWidget(api_group)
        
        # 模型设置组
        model_group = QGroupBox("模型设置")
        model_layout = QVBoxLayout(model_group)
        
        # 模型名称
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("模型名称:"))
        self.model_edit = QLineEdit("Qwen2.5-VL-7B")
        name_layout.addWidget(self.model_edit)
        model_layout.addLayout(name_layout)
        
        # 最大token数
        token_layout = QHBoxLayout()
        token_layout.addWidget(QLabel("最大Token数:"))
        self.token_edit = QLineEdit("4096")
        token_layout.addWidget(self.token_edit)
        model_layout.addLayout(token_layout)
        
        # 经典配置选择
        config_layout = QHBoxLayout()
        config_layout.addWidget(QLabel("经典配置:"))
        self.config_combo = QComboBox()
        self.config_combo.addItems(["technical", "creative", "balanced"])
        config_layout.addWidget(self.config_combo)
        
        # 温度参数
        temp_layout = QHBoxLayout()
        temp_layout.addWidget(QLabel("温度参数:"))
        self.temp_edit = QLineEdit("0.3")
        temp_layout.addWidget(self.temp_edit)
        
        # Top-p参数
        top_p_layout = QHBoxLayout()
        top_p_layout.addWidget(QLabel("Top-p参数:"))
        self.top_p_edit = QLineEdit("0.65")
        top_p_layout.addWidget(self.top_p_edit)
        
        model_layout.addLayout(config_layout)
        model_layout.addLayout(temp_layout)
        model_layout.addLayout(top_p_layout)
        main_layout.addWidget(model_group)
        
        # 图标设置组
        icon_group = QGroupBox("图标设置")
        icon_layout = QVBoxLayout(icon_group)
        
        # 应用图标设置
        app_icon_layout = QHBoxLayout()
        app_icon_layout.addWidget(QLabel("应用图标:"))
        self.app_icon_edit = QLineEdit("./icons/CASC-LOGO-transparency.png")
        app_icon_layout.addWidget(self.app_icon_edit)
        app_icon_btn = QPushButton("浏览...")
        app_icon_btn.clicked.connect(lambda: self.browse_icon("app"))
        app_icon_layout.addWidget(app_icon_btn)
        icon_layout.addLayout(app_icon_layout)
        
        # 窗口图标设置
        window_icon_layout = QHBoxLayout()
        window_icon_layout.addWidget(QLabel("窗口图标:"))
        self.window_icon_edit = QLineEdit("./icons/CASC-LOGO-transparency.png")
        window_icon_layout.addWidget(self.window_icon_edit)
        window_icon_btn = QPushButton("浏览...")
        window_icon_btn.clicked.connect(lambda: self.browse_icon("window"))
        window_icon_layout.addWidget(window_icon_btn)
        icon_layout.addLayout(window_icon_layout)
        
        # 头像图片设置
        avatar_layout = QHBoxLayout()
        avatar_layout.addWidget(QLabel("头像图片:"))
        self.avatar_edit = QLineEdit("./icons/star.png")
        avatar_layout.addWidget(self.avatar_edit)
        avatar_btn = QPushButton("浏览...")
        avatar_btn.clicked.connect(lambda: self.browse_icon("avatar"))
        avatar_layout.addWidget(avatar_btn)
        icon_layout.addLayout(avatar_layout)
        
        # 背景图片设置
        bg_layout = QHBoxLayout()
        bg_layout.addWidget(QLabel("背景图片:"))
        self.bg_edit = QLineEdit("./icons/lulingqi.png")
        bg_layout.addWidget(self.bg_edit)
        bg_btn = QPushButton("浏览...")
        bg_btn.clicked.connect(lambda: self.browse_icon("bg"))
        bg_layout.addWidget(bg_btn)
        icon_layout.addLayout(bg_layout)
        
        main_layout.addWidget(icon_group)
        
        # 按钮布局
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("保存")
        save_btn.clicked.connect(self.accept)
        btn_layout.addWidget(save_btn)
        
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        main_layout.addLayout(btn_layout)
        
        self.setLayout(main_layout)
        
        # 配置经典参数选项
        self.config = {
            "technical": {"top_p": 0.65, "temperature": 0.3},
            "creative": {"top_p": 0.9, "temperature": 0.8},
            "balanced": {"top_p": 0.8, "temperature": 0.6}
        }
        self.config_combo.currentIndexChanged.connect(self.update_config)
    
    def browse_icon(self, icon_type):
        """浏览并选择图标文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            f"选择{icon_type}图标", 
            "", 
            "图片文件 (*.png *.jpg *.jpeg *.bmp)"
        )
        
        if file_path:
            if icon_type == "app":
                self.app_icon_edit.setText(file_path)
            elif icon_type == "window":
                self.window_icon_edit.setText(file_path)
            elif icon_type == "avatar":
                self.avatar_edit.setText(file_path)
            elif icon_type == "bg":
                self.bg_edit.setText(file_path)
    
    def update_config(self):
        """根据选择的经典配置更新参数"""
        config_name = self.config_combo.currentText()
        config = self.config.get(config_name, {})
        self.temp_edit.setText(str(config.get("temperature", 0.3)))
        self.top_p_edit.setText(str(config.get("top_p", 0.65)))
    
    def get_values(self):
        """获取所有设置值"""
        return {
            "api_url": self.url_edit.text(),
            "api_key": self.key_edit.text(),
            "model_name": self.model_edit.text(),
            "max_tokens": int(self.token_edit.text()),
            "temperature": float(self.temp_edit.text()),
            "top_p": float(self.top_p_edit.text()),
            "app_icon": self.app_icon_edit.text(),
            "window_icon": self.window_icon_edit.text(),
            "avatar": self.avatar_edit.text(),
            "bg_image": self.bg_edit.text()
        }

class HelpDialog(QDialog):
    """帮助文档对话框"""
    def __init__(self, help_data, parent=None):
        super().__init__(parent)
        self.setWindowTitle("使用帮助")
        self.setGeometry(100, 100, 500, 600)
        
        layout = QVBoxLayout(self)
        
        # 帮助主题按钮
        btn_layout = QHBoxLayout()
        self.btn_select = QPushButton("数据筛选使用说明")
        self.btn_select.clicked.connect(lambda: self.show_help_content("data_select"))
        btn_layout.addWidget(self.btn_select)
        
        self.btn_generate = QPushButton("数据制备使用说明")
        self.btn_generate.clicked.connect(lambda: self.show_help_content("data_generate"))
        btn_layout.addWidget(self.btn_generate)
        
        self.btn_refine = QPushButton("数据精炼使用说明")
        self.btn_refine.clicked.connect(lambda: self.show_help_content("data_refine"))
        btn_layout.addWidget(self.btn_refine)
        layout.addLayout(btn_layout)
        
        # 帮助内容显示
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        layout.addWidget(self.text_edit)
        
        # 关闭按钮
        btn_close = QPushButton("关闭")
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close)
        
        self.help_data = help_data
    
    def show_help_content(self, module):
        """显示指定模块的帮助内容"""
        content = self.help_data.get(module, "帮助内容未找到")
        self.text_edit.setPlainText(content)

class WelcomePage(QWidget):
    """欢迎页面组件 - 优化水平无缝滚动"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.bg_pixmap = None
        self.setStyleSheet("background-color: transparent;")
        
        # 滚动效果初始化
        self.scroll_offset = 0
        self.scroll_speed = 2  # 增加滚动速度
        self.scaled_width = 0
        self.scaled_height = 0
        
        # 滚动定时器 - 使用更快的刷新率
        self.scroll_timer = QTimer(self)
        self.scroll_timer.timeout.connect(self.update_scroll)
        self.scroll_timer.start(16)  # 约60FPS (1000ms/60≈16ms)
        
        layout = QVBoxLayout(self)
        layout.addStretch()
        
        # 欢迎标题
        welcome_container = QWidget()
        welcome_container_layout = QHBoxLayout(welcome_container)
        welcome_container_layout.setContentsMargins(0, 0, 0, 0)
        
        self.welcome = QLabel("欢迎使用多模态数据科学工具箱")
        self.welcome.setFont(QFont("Segoe UI", 18, QFont.Bold))
        self.welcome.setStyleSheet("color: #0059b3; background-color: rgba(230, 247, 255, 13); padding: 15px; border-radius: 10px;")
        self.welcome.setAlignment(Qt.AlignCenter)
        
        welcome_container_layout.addStretch()
        welcome_container_layout.addWidget(self.welcome)
        welcome_container_layout.addStretch()
        layout.addWidget(welcome_container)
        
        # 提示信息
        hint_container = QWidget()
        hint_container_layout = QHBoxLayout(hint_container)
        hint_container_layout.setContentsMargins(0, 0, 0, 0)
        
        self.hint = QLabel("请从侧边栏选择功能模块")
        self.hint.setFont(QFont("Segoe UI", 10))
        self.hint.setStyleSheet("color: #3399ff; background-color: rgba(230, 247, 255, 13); padding: 15px; border-radius: 10px;")
        self.hint.setAlignment(Qt.AlignCenter)
        
        hint_container_layout.addStretch()
        hint_container_layout.addWidget(self.hint)
        hint_container_layout.addStretch()
        layout.addWidget(hint_container)
        
        layout.addStretch()
    
    def resizeEvent(self, event):
        """调整标签宽度为窗口宽度的90%"""
        super().resizeEvent(event)
        label_width = int(self.width() * 0.9)
        self.welcome.setMaximumWidth(label_width)
        self.hint.setMaximumWidth(label_width)
        
        # 窗口大小改变时重置滚动参数
        self.update_scroll_params()
    
    def setBackground(self, pixmap):
        """设置背景图片并重置滚动参数"""
        self.bg_pixmap = pixmap
        self.update_scroll_params()
        self.update()
    
    def update_scroll_params(self):
        """计算并更新滚动所需的参数"""
        if self.bg_pixmap and not self.bg_pixmap.isNull():
            # 计算缩放尺寸 - 高度等于窗口高度，宽度按比例缩放
            target_height = self.height()
            self.scaled_height = target_height
            self.scaled_width = int(self.bg_pixmap.width() * (target_height / self.bg_pixmap.height()))
            
            # 重置滚动位置
            self.scroll_offset = 0
            
            # 调整滚动速度基于图片宽度
            self.scroll_speed = max(1, int(self.scaled_width / 400))  # max(1, int(self.scaled_width / 200)) or 1(integer(smaller->slower))
    
    def update_scroll(self):
        """更新滚动位置 - 水平无缝滚动"""
        if self.scaled_width > 0:
            self.scroll_offset -= self.scroll_speed
            
            # 当图片完全移出屏幕时重置位置
            if self.scroll_offset <= -self.scaled_width:
                self.scroll_offset += self.scaled_width
            
            # 请求重绘
            self.update()
    
    def paintEvent(self, event):
        """绘制背景和滚动效果 - 水平无缝滚动"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        painter.fillRect(self.rect(), Qt.white)
        
        if self.bg_pixmap and not self.bg_pixmap.isNull():
            # 创建缩放后的图片
            scaled_pixmap = self.bg_pixmap.scaled(
                self.scaled_width, 
                self.scaled_height,
                Qt.IgnoreAspectRatio,
                Qt.SmoothTransformation
            )
            
            painter.setOpacity(0.3)
            
            # 计算绘制位置
            current_x = self.scroll_offset
            window_width = self.width()
            
            # 绘制图片直到覆盖整个窗口
            while current_x < window_width:
                painter.drawPixmap(current_x, 0, scaled_pixmap)
                current_x += self.scaled_width
            
            painter.setOpacity(1.0)
        
        super().paintEvent(event)

class MainWindow(QMainWindow):
    """主窗口类"""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("多模态数据科学工具箱")
        self.setGeometry(300, 100, 1000, 700)
        
        # 先初始化设置
        self.settings = {
            "api_url": "http://localhost:8089/v1",
            "api_key": "no-api-key-required",
            "model_name": "Qwen2.5-VL-7B",
            "max_tokens": 4096,
            "temperature": 0.3,
            "top_p": 0.65,
            "app_icon": "./icons/CASC-LOGO-transparency.png",
            "window_icon": "./icons/CASC-LOGO-transparency.png",
            "avatar": "./icons/star.png",
            "bg_image": "./icons/lulingqi.png"
        }
        
        # 主界面布局
        main_widget = QWidget()
        main_widget.setStyleSheet("background-color: #ffffff;")
        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        self.splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(self.splitter)
        
        # 侧边栏 - 现在可以安全访问 self.settings
        sidebar = self.create_sidebar()
        self.splitter.addWidget(sidebar)
        
        # 内容区域
        self.content = QStackedWidget()
        self.content.setStyleSheet("background-color: #ffffff;")
        
        # 欢迎页面
        self.init_page = WelcomePage()
        self.init_page.setStyleSheet("background-color: transparent;")
        
        # 功能页面
        self.select_page = self.create_page("border: 1px solid #cce6ff; border-radius: 10px; background-color: #ffffff;")
        self.generate_page = self.create_page("border: 1px solid #cce6ff; border-radius: 10px; background-color: #ffffff;")
        self.refine_page = self.create_page("border: 1px solid #cce6ff; border-radius: 10px; background-color: #ffffff;")
        
        self.content.addWidget(self.init_page)
        self.content.addWidget(self.select_page)
        self.content.addWidget(self.generate_page)
        self.content.addWidget(self.refine_page)
        
        self.splitter.addWidget(self.content)
        self.splitter.setSizes([150, 850])
        self.splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #cce6ff;
                width: 5px;
            }
            QSplitter::handle:hover {
                background-color: #99ccff;
            }
        """)
        
        self.setCentralWidget(main_widget)
        
        # 模块状态初始化
        self.data_select_imported = False
        self.data_generate_imported = False
        self.data_refine_imported = False
        self.data_select_window = None
        self.data_generate_window = None
        self.data_refine_window = None
        
        # 设置背景图片
        self.update_background_image()
    
    def create_page(self, style):
        """创建带样式的页面容器"""
        page = QWidget()
        page.setStyleSheet(style)
        return page
    
    def create_sidebar(self):
        """创建侧边栏组件"""
        sidebar = QWidget()
        sidebar.setMinimumWidth(150)
        sidebar.setMaximumWidth(250)
        sidebar.setStyleSheet("background-color: #f0f9ff; border-right: 1px solid #cce6ff;")
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(5, 5, 5, 5)
        sidebar_layout.setSpacing(5)
        
        # 标题区域
        title_layout = QHBoxLayout()
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(5)
        
        # 使用默认头像
        if os.path.exists(self.settings["avatar"]):
            logo_label = QLabel()
            logo_pixmap = QPixmap(self.settings["avatar"]).scaled(40, 40, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo_label.setPixmap(logo_pixmap)
            logo_label.setAlignment(Qt.AlignCenter)
            title_layout.addWidget(logo_label)
        
        title = QLabel("多模态数据治理工具平台")
        title.setFont(QFont("Segoe UI", 10, QFont.Bold))
        title.setStyleSheet("color: #0059b3; padding: 6px; background-color: #e6f2ff; border-radius: 8px; border: 1px solid #99ccff;")
        title.setAlignment(Qt.AlignCenter)
        title.setWordWrap(True)
        title_layout.addWidget(title)
        sidebar_layout.addLayout(title_layout)
        
        # 分隔线
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet("background-color: #99ccff; height: 2px;")
        sidebar_layout.addWidget(separator)
        
        # 功能按钮
        button_container = QWidget()
        button_container.setStyleSheet("background-color: transparent;")
        button_layout = QVBoxLayout(button_container)
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(5)
        
        self.btn_select = TechButton("数据筛选", "./icons/set_icon.png")
        self.btn_select.clicked.connect(self.show_data_select)
        button_layout.addWidget(self.btn_select)
        
        self.btn_generate = TechButton("数据制备", "./icons/set_icon.png")
        self.btn_generate.clicked.connect(self.show_data_generate)
        button_layout.addWidget(self.btn_generate)
        
        self.btn_refine = TechButton("数据精炼", "./icons/set_icon.png")
        self.btn_refine.clicked.connect(self.show_data_refine)
        button_layout.addWidget(self.btn_refine)
        
        self.btn_api = TechButton("设置", "./icons/set_icon.png")
        self.btn_api.clicked.connect(self.show_settings_dialog)
        button_layout.addWidget(self.btn_api)
        
        self.btn_help = TechButton("帮助", "./icons/set_icon.png")
        self.btn_help.clicked.connect(self.show_help)
        button_layout.addWidget(self.btn_help)
        
        sidebar_layout.addWidget(button_container)
        sidebar_layout.addStretch(1)
        
        # 作者信息
        author_frame = QFrame()
        author_frame.setStyleSheet("background-color: #e6f2ff; border-radius: 8px; padding: 6px; border: 1px solid #cce6ff;")
        author_layout = QVBoxLayout(author_frame)
        
        org_label = QLabel("多模态模型组")
        org_label.setFont(QFont("Segoe UI", 8))
        org_label.setStyleSheet("color: #0066cc;")
        org_label.setAlignment(Qt.AlignCenter)
        author_layout.addWidget(org_label)
        
        copyright_label = QLabel("@2025 版权所有")
        copyright_label.setFont(QFont("Segoe UI", 7))
        copyright_label.setStyleSheet("color: #3399ff;")
        copyright_label.setAlignment(Qt.AlignCenter)
        author_layout.addWidget(copyright_label)
        
        author_label = QLabel("作者: Lin, X")
        author_label.setFont(QFont("Segoe UI", 8))
        author_label.setStyleSheet("color: #0066cc;")
        author_label.setAlignment(Qt.AlignCenter)
        author_layout.addWidget(author_label)
        
        sidebar_layout.addWidget(author_frame)
        
        # 点击标题返回欢迎界面
        title.mousePressEvent = lambda event: self.content.setCurrentIndex(0)
        
        return sidebar
    
    def update_background_image(self):
        """更新背景图片"""
        if os.path.exists(self.settings["bg_image"]):
            pixmap = QPixmap(self.settings["bg_image"])
            self.init_page.setBackground(pixmap)
    
    def show_settings_dialog(self):
        """显示设置对话框"""
        dialog = SettingsDialog(self)
        dialog.url_edit.setText(self.settings["api_url"])
        dialog.key_edit.setText(self.settings["api_key"])
        dialog.model_edit.setText(self.settings["model_name"])
        dialog.token_edit.setText(str(self.settings["max_tokens"]))
        dialog.temp_edit.setText(str(self.settings["temperature"]))
        dialog.top_p_edit.setText(str(self.settings["top_p"]))
        dialog.app_icon_edit.setText(self.settings["app_icon"])
        dialog.window_icon_edit.setText(self.settings["window_icon"])
        dialog.avatar_edit.setText(self.settings["avatar"])
        dialog.bg_edit.setText(self.settings["bg_image"])
        
        if dialog.exec_():
            new_settings = dialog.get_values()
            self.settings.update(new_settings)
            
            # 更新背景图片
            self.update_background_image()
            
            # 更新应用图标
            if os.path.exists(self.settings["app_icon"]):
                QApplication.instance().setWindowIcon(QIcon(self.settings["app_icon"]))
            
            # 更新窗口图标
            if os.path.exists(self.settings["window_icon"]):
                self.setWindowIcon(QIcon(self.settings["window_icon"]))
            
            # 更新已加载模块的配置
            if self.data_refine_window:
                self.data_refine_window.vlm_api_url = self.settings["api_url"]
                self.data_refine_window.api_key = self.settings["api_key"]
                self.data_refine_window.model_name = self.settings["model_name"]
                self.data_refine_window.max_tokens = self.settings["max_tokens"]
                self.data_refine_window.temperature = self.settings["temperature"]
                self.data_refine_window.top_p = self.settings["top_p"]
            
            if self.data_generate_window:
                self.data_generate_window.model_name = self.settings["model_name"]
                self.data_generate_window.max_tokens = self.settings["max_tokens"]
                self.data_generate_window.temperature = self.settings["temperature"]
                self.data_generate_window.top_p = self.settings["top_p"]
    
    def show_help(self):
        """显示帮助对话框"""
        try:
            with open('help.json', 'r', encoding='utf-8') as f:
                help_data = json.load(f)
        except:
            help_data = {
                "data_select": "数据筛选模块帮助内容未加载",
                "data_generate": "数据制备模块帮助内容未加载",
                "data_refine": "数据精炼模块帮助内容未加载"
            }
        
        dialog = HelpDialog(help_data, self)
        dialog.exec_()
    
    def show_data_select(self):
        """显示数据筛选页面"""
        if not self.data_select_imported:
            try:
                import importlib
                data_select = importlib.import_module('data_select')
                self.data_select_imported = True
                self.data_select_window = data_select.ImageDataCleaner()
                self.data_select_window.image_display.setStyleSheet(
                    "border: 1px solid #cce6ff; background-color: #ffffff;")
                self.apply_button_style(self.data_select_window)
                layout = QVBoxLayout(self.select_page)
                layout.setContentsMargins(10, 10, 10, 10)
                layout.addWidget(self.data_select_window)
            except Exception as e:
                self.show_error_page(self.select_page, str(e))
        self.content.setCurrentIndex(1)
    
    def show_data_generate(self):
        """显示数据制备页面"""
        if not self.data_generate_imported:
            try:
                import importlib
                data_generate = importlib.import_module('data_generate')
                self.data_generate_imported = True
                self.data_generate_window = data_generate.DataGenerator()
                self.apply_button_style(self.data_generate_window)
                
                # 传递设置参数
                self.data_generate_window.model_name = self.settings["model_name"]
                self.data_generate_window.max_tokens = self.settings["max_tokens"]
                self.data_generate_window.temperature = self.settings["temperature"]
                self.data_generate_window.top_p = self.settings["top_p"]
                
                layout = QVBoxLayout(self.generate_page)
                layout.setContentsMargins(0, 0, 0, 0)
                layout.addWidget(self.data_generate_window)
            except Exception as e:
                self.show_error_page(self.generate_page, str(e))
        self.content.setCurrentIndex(2)
    
    def show_data_refine(self):
        """显示数据精炼页面"""
        if not self.data_refine_imported:
            try:
                import importlib
                data_refine = importlib.import_module('data_refine')
                self.data_refine_imported = True
                self.data_refine_window = data_refine.ImageTextAnnotator()
                self.data_refine_window.setStyleSheet("""
                    QFrame, QGroupBox, QWidget {
                        background-color: #ffffff;
                        color: #000000;
                    }
                    QTextEdit, QLineEdit, QListWidget {
                        background-color: #ffffff;
                        color: #000000;
                        border: 1px solid #cce6ff;
                    }
                """)
                self.apply_button_style(self.data_refine_window)
                
                # 传递设置参数
                self.data_refine_window.vlm_api_url = self.settings["api_url"]
                self.data_refine_window.api_key = self.settings["api_key"]
                self.data_refine_window.model_name = self.settings["model_name"]
                self.data_refine_window.max_tokens = self.settings["max_tokens"]
                self.data_refine_window.temperature = self.settings["temperature"]
                self.data_refine_window.top_p = self.settings["top_p"]
                
                # 移除内置帮助菜单
                help_menu = self.data_refine_window.menuBar().findChild(QMenu, "帮助")
                if help_menu:
                    self.data_refine_window.menuBar().removeAction(help_menu.menuAction())
                
                layout = QVBoxLayout(self.refine_page)
                layout.setContentsMargins(0, 0, 0, 0)
                layout.addWidget(self.data_refine_window)
            except Exception as e:
                self.show_error_page(self.refine_page, str(e))
        self.content.setCurrentIndex(3)
    
    def show_error_page(self, page, error):
        """在指定页面显示错误信息"""
        error_label = QLabel(f"导入错误: {error}")
        error_label.setAlignment(Qt.AlignCenter)
        error_label.setStyleSheet("color: #ff5555; font-size: 16px;")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.addWidget(error_label)
    
    def apply_button_style(self, widget):
        """应用统一按钮样式"""
        for child in widget.findChildren(QPushButton):
            if not isinstance(child, TechButton):
                child.setStyleSheet("""
                    QPushButton {
                        background-color: #e6f7ff;
                        color: #0066cc;
                        border: 1px solid #66b3ff;
                        border-radius: 8px;
                        padding: 5px;
                        margin: 2px;
                        font: bold 9pt "Segoe UI";
                    }
                    QPushButton:hover {
                        background-color: #d1e8ff;
                        border: 1px solid #3399ff;
                    }
                    QPushButton:pressed {
                        background-color: #b3d9ff;
                    }
                """)
                child.setFont(QFont("Segoe UI", 9, QFont.Bold))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    # 设置应用调色板
    palette = app.palette()
    palette.setColor(QPalette.Window, QColor(255, 255, 255))
    palette.setColor(QPalette.WindowText, QColor(0, 0, 0))
    palette.setColor(QPalette.Base, QColor(255, 255, 255))
    palette.setColor(QPalette.AlternateBase, QColor(240, 249, 255))
    palette.setColor(QPalette.ToolTipBase, QColor(255, 255, 255))
    palette.setColor(QPalette.ToolTipText, QColor(0, 0, 0))
    palette.setColor(QPalette.Text, QColor(0, 0, 0))
    palette.setColor(QPalette.Button, QColor(230, 247, 255))
    palette.setColor(QPalette.ButtonText, QColor(0, 89, 179))
    palette.setColor(QPalette.BrightText, Qt.red)
    palette.setColor(QPalette.Link, QColor(0, 102, 204))
    palette.setColor(QPalette.Highlight, QColor(204, 230, 255))
    palette.setColor(QPalette.HighlightedText, QColor(0, 0, 0))
    app.setPalette(palette)
    
    # 全局样式表
    app.setStyleSheet("""
        QPushButton {
            background-color: #e6f7ff;
            color: #0066cc;
            border: 1px solid #66b3ff;
            border-radius: 8px;
            padding: 5px;
            margin: 2px;
            font: bold 9pt "Segoe UI";
        }
        QPushButton:hover {
            background-color: #d1e8ff;
            border: 1px solid #3399ff;
        }
        QPushButton:pressed {
            background-color: #b3d9ff;
        }
    """)
    
    # 创建并显示主窗口
    window = MainWindow()
    
    # 设置应用图标（在主窗口创建后设置）
    if os.path.exists(window.settings["window_icon"]):
        app.setWindowIcon(QIcon(window.settings["window_icon"]))
    
    window.show()
    sys.exit(app.exec_())
