import sys
import os
import json
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QStackedWidget,
                             QFrame, QSplitter, QSizePolicy, QDialog, QLineEdit,
                             QTextEdit, QMenu)
from PyQt5.QtCore import Qt, QSize, QTimer
from PyQt5.QtGui import QFont, QIcon, QColor, QPalette, QPixmap, QPainter, QLinearGradient

class TechButton(QPushButton):
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

class APIDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("API设置")
        layout = QVBoxLayout()
        
        url_layout = QHBoxLayout()
        url_layout.addWidget(QLabel("API_URL:"))
        self.url_edit = QLineEdit()
        url_layout.addWidget(self.url_edit)
        layout.addLayout(url_layout)
        
        key_layout = QHBoxLayout()
        key_layout.addWidget(QLabel("API_KEY:"))
        self.key_edit = QLineEdit()
        key_layout.addWidget(self.key_edit)
        layout.addLayout(key_layout)
        
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("保存")
        save_btn.clicked.connect(self.accept)
        btn_layout.addWidget(save_btn)
        
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
    
    def get_values(self):
        return self.url_edit.text(), self.key_edit.text()

class HelpDialog(QDialog):
    def __init__(self, help_data, parent=None):
        super().__init__(parent)
        self.setWindowTitle("使用帮助")
        self.setGeometry(100, 100, 500, 600)
        
        layout = QVBoxLayout(self)
        
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
        
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        layout.addWidget(self.text_edit)
        
        btn_close = QPushButton("关闭")
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close)
        
        self.help_data = help_data
    
    def show_help_content(self, module):
        content = self.help_data.get(module, "帮助内容未找到")
        self.text_edit.setPlainText(content)

class WelcomePage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.bg_pixmap = None
        self.setStyleSheet("background-color: transparent;")
        
        # 滚动相关变量
        self.scroll_direction = None  # 'horizontal' 或 'vertical'
        self.scroll_offset = 0
        self.scroll_speed = 1  # 滚动速度（像素/帧）
        self.scaled_width = 0
        self.scaled_height = 0
        
        # 初始化定时器用于滚动
        self.scroll_timer = QTimer(self)
        self.scroll_timer.timeout.connect(self.update_scroll)
        self.scroll_timer.start(30)  # 每30毫秒更新一次
        
        layout = QVBoxLayout(self)
        layout.addStretch()
        
        # 创建容器用于居中标签
        welcome_container = QWidget()
        welcome_container_layout = QHBoxLayout(welcome_container)
        welcome_container_layout.setContentsMargins(0, 0, 0, 0)
        
        self.welcome = QLabel("欢迎使用多模态数据科学工具箱")
        self.welcome.setFont(QFont("Segoe UI", 18, QFont.Bold))
        # 设置为5%透明度 (255 * 0.05 ≈ 13)
        self.welcome.setStyleSheet("color: #0059b3; background-color: rgba(230, 247, 255, 13); padding: 15px; border-radius: 10px;")
        self.welcome.setAlignment(Qt.AlignCenter)
        
        # 添加水平伸展使标签居中
        welcome_container_layout.addStretch()
        welcome_container_layout.addWidget(self.welcome)
        welcome_container_layout.addStretch()
        
        layout.addWidget(welcome_container)
        
        # 创建容器用于居中标签
        hint_container = QWidget()
        hint_container_layout = QHBoxLayout(hint_container)
        hint_container_layout.setContentsMargins(0, 0, 0, 0)
        
        self.hint = QLabel("请从侧边栏选择功能模块")
        self.hint.setFont(QFont("Segoe UI", 10))
        # 设置为5%透明度
        self.hint.setStyleSheet("color: #3399ff; background-color: rgba(230, 247, 255, 13); padding: 15px; border-radius: 10px;")
        self.hint.setAlignment(Qt.AlignCenter)
        
        # 添加水平伸展使标签居中
        hint_container_layout.addStretch()
        hint_container_layout.addWidget(self.hint)
        hint_container_layout.addStretch()
        
        layout.addWidget(hint_container)
        
        layout.addStretch()
    
    def resizeEvent(self, event):
        """调整标签宽度为窗口宽度的90%"""
        super().resizeEvent(event)
        label_width = int(self.width() * 0.9)  # 缩短10%
        self.welcome.setMaximumWidth(label_width)
        self.hint.setMaximumWidth(label_width)
    
    def setBackground(self, pixmap):
        self.bg_pixmap = pixmap
        self.update()
    
    def update_scroll(self):
        """更新滚动位置"""
        if self.scroll_direction == 'horizontal' and self.scaled_width > 0:
            self.scroll_offset -= self.scroll_speed
            if self.scroll_offset <= -self.scaled_width:
                self.scroll_offset += self.scaled_width
        elif self.scroll_direction == 'vertical' and self.scaled_height > 0:
            self.scroll_offset -= self.scroll_speed
            if self.scroll_offset <= -self.scaled_height:
                self.scroll_offset += self.scaled_height
        
        self.update()  # 触发重绘
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        
        # 首先绘制白色背景
        painter.fillRect(self.rect(), Qt.white)
        
        if self.bg_pixmap and not self.bg_pixmap.isNull():
            # 计算窗口和图片的宽高比
            window_ratio = self.width() / self.height()
            pixmap_ratio = self.bg_pixmap.width() / self.bg_pixmap.height()
            
            # 计算缩放后的大小 - 修正滚动效果
            if window_ratio > pixmap_ratio:
                # 窗口更宽，按高度缩放
                self.scaled_height = self.height()
                self.scaled_width = int(self.bg_pixmap.width() * (self.scaled_height / self.bg_pixmap.height()))
                # 水平方向有空白
                self.scroll_direction = 'horizontal'
            else:
                # 窗口更高，按宽度缩放
                self.scaled_width = self.width()
                self.scaled_height = int(self.bg_pixmap.height() * (self.scaled_width / self.bg_pixmap.width()))
                # 垂直方向有空白
                self.scroll_direction = 'vertical'
            
            # 创建缩放后的图片
            scaled_pixmap = self.bg_pixmap.scaled(
                self.scaled_width, 
                self.scaled_height, 
                Qt.KeepAspectRatio,  # 保持宽高比
                Qt.SmoothTransformation
            )
            
            # 应用半透明效果
            painter.setOpacity(0.3)  # 30%透明度
            
            # 根据滚动方向绘制背景图片
            if self.scroll_direction == 'horizontal':
                # 水平滚动 - 从右向左
                x1 = self.scroll_offset
                y = int((self.height() - self.scaled_height) / 2)
                
                # 绘制两张图片实现连续滚动
                painter.drawPixmap(x1, y, scaled_pixmap)
                painter.drawPixmap(x1 + self.scaled_width, y, scaled_pixmap)
            elif self.scroll_direction == 'vertical':
                # 垂直滚动 - 从下向上
                x = int((self.width() - self.scaled_width) / 2)
                y1 = self.scroll_offset
                
                # 绘制两张图片实现连续滚动
                painter.drawPixmap(x, y1, scaled_pixmap)
                painter.drawPixmap(x, y1 + self.scaled_height, scaled_pixmap)
            
            # 重置透明度
            painter.setOpacity(1.0)
        
        super().paintEvent(event)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("多模态数据科学工具箱")
        self.setGeometry(300, 100, 1000, 700)
        
        main_widget = QWidget()
        main_widget.setStyleSheet("background-color: #ffffff;")
        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        self.splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(self.splitter)
        
        sidebar = QWidget()
        sidebar.setMinimumWidth(150)
        sidebar.setMaximumWidth(250)
        sidebar.setStyleSheet("background-color: #f0f9ff; border-right: 1px solid #cce6ff;")
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(5, 5, 5, 5)
        sidebar_layout.setSpacing(5)
        
        title_layout = QHBoxLayout()
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(5)
        
        if os.path.exists("./icons/star.png"):
            logo_label = QLabel()
            logo_pixmap = QPixmap("./icons/star.png").scaled(40, 40, Qt.KeepAspectRatio, Qt.SmoothTransformation)
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
        
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet("background-color: #99ccff; height: 2px;")
        sidebar_layout.addWidget(separator)
        
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
        
        self.btn_api = TechButton("API设置", "./icons/set_icon.png")
        self.btn_api.clicked.connect(self.show_api_dialog)
        button_layout.addWidget(self.btn_api)
        
        self.btn_help = TechButton("帮助", "./icons/set_icon.png")
        self.btn_help.clicked.connect(self.show_help)
        button_layout.addWidget(self.btn_help)
        
        sidebar_layout.addWidget(button_container)
        sidebar_layout.addStretch(1)
        
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
        
        self.content = QStackedWidget()
        self.content.setStyleSheet("background-color: #ffffff;")
        
        # 创建自定义欢迎页面
        self.init_page = WelcomePage()
        self.init_page.setStyleSheet("background-color: transparent;")
        
        # 设置背景图片
        icon_path = "./icons/lulingqi.png"
        if os.path.exists(icon_path):
            pixmap = QPixmap(icon_path)
            self.init_page.setBackground(pixmap)
        
        self.select_page = QWidget()
        self.select_page.setStyleSheet("border: 1px solid #cce6ff; border-radius: 10px; background-color: #ffffff;")
        self.generate_page = QWidget()
        self.generate_page.setStyleSheet("border: 1px solid #cce6ff; border-radius: 10px; background-color: #ffffff;")
        self.refine_page = QWidget()
        self.refine_page.setStyleSheet("border: 1px solid #cce6ff; border-radius: 10px; background-color: #ffffff;")
        
        self.content.addWidget(self.init_page)
        self.content.addWidget(self.select_page)
        self.content.addWidget(self.generate_page)
        self.content.addWidget(self.refine_page)
        
        self.splitter.addWidget(sidebar)
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
        
        self.data_select_imported = False
        self.data_generate_imported = False
        self.data_refine_imported = False
        self.data_select_window = None
        self.data_generate_window = None
        self.data_refine_window = None
        self.api_url = "http://localhost:8089/v1"
        self.api_key = "no-api-key-required"
        
        # 点击标题返回欢迎界面
        title.mousePressEvent = lambda event: self.content.setCurrentIndex(0)
    
    def show_api_dialog(self):
        dialog = APIDialog(self)
        dialog.url_edit.setText(self.api_url)
        dialog.key_edit.setText(self.api_key)
        if dialog.exec_():
            self.api_url, self.api_key = dialog.get_values()
            if self.data_refine_window:
                self.data_refine_window.vlm_api_url = self.api_url
                self.data_refine_window.api_key = self.api_key
    
    def show_help(self):
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
                error_label = QLabel(f"导入错误: {str(e)}")
                error_label.setAlignment(Qt.AlignCenter)
                error_label.setStyleSheet("color: #ff5555; font-size: 16px;")
                layout = QVBoxLayout(self.select_page)
                layout.setContentsMargins(10, 10, 10, 10)
                layout.addWidget(error_label)
        self.content.setCurrentIndex(1)
    
    def show_data_generate(self):
        if not self.data_generate_imported:
            try:
                import importlib
                data_generate = importlib.import_module('data_generate')
                self.data_generate_imported = True
                self.data_generate_window = data_generate.DataGenerator()
                self.apply_button_style(self.data_generate_window)
                layout = QVBoxLayout(self.generate_page)
                layout.setContentsMargins(0, 0, 0, 0)
                layout.addWidget(self.data_generate_window)
            except Exception as e:
                error_label = QLabel(f"导入错误: {str(e)}")
                error_label.setAlignment(Qt.AlignCenter)
                error_label.setStyleSheet("color: #ff5555; font-size: 16px;")
                layout = QVBoxLayout(self.generate_page)
                layout.addWidget(error_label)
        self.content.setCurrentIndex(2)
    
    def show_data_refine(self):
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
                
                help_menu = self.data_refine_window.menuBar().findChild(QMenu, "帮助")
                if help_menu:
                    self.data_refine_window.menuBar().removeAction(help_menu.menuAction())
                
                layout = QVBoxLayout(self.refine_page)
                layout.setContentsMargins(0, 0, 0, 0)
                layout.addWidget(self.data_refine_window)
            except Exception as e:
                error_label = QLabel(f"导入错误: {str(e)}")
                error_label.setAlignment(Qt.AlignCenter)
                error_label.setStyleSheet("color: #ff5555; font-size: 16px;")
                layout = QVBoxLayout(self.refine_page)
                layout.addWidget(error_label)
        self.content.setCurrentIndex(3)
    
    def apply_button_style(self, widget):
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
    
    if os.path.exists("./icons/CASC-LOGO-transparency.png"):
        app.setWindowIcon(QIcon("./icons/CASC-LOGO-transparency.png"))
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())