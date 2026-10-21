import sys
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QStackedWidget,
                             QFrame, QSplitter, QSizePolicy, QDialog, QLineEdit,
                             QTextEdit, QPushButton)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QFont, QIcon, QColor, QPalette, QPixmap


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

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("多模态数据科学工具箱")
        self.setGeometry(300, 100, 1000, 700)
        if os.path.exists("./icons/CASC-LOGO-transparency.png"):
            self.setWindowIcon(QIcon("./icons/CASC-LOGO-transparency.png"))
        
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
        
        if os.path.exists("./icons/CASC-LOGO-transparency.png"):
            logo_label = QLabel()
            logo_pixmap = QPixmap("./icons/CASC-LOGO-transparency.png").scaled(40, 40, Qt.KeepAspectRatio, Qt.SmoothTransformation)
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
        org_label.setWordWrap(True)
        author_layout.addWidget(org_label)
        
        copyright_label = QLabel("@2025 版权所有")
        copyright_label.setFont(QFont("Segoe UI", 7))
        copyright_label.setStyleSheet("color: #3399ff;")
        copyright_label.setAlignment(Qt.AlignCenter)
        copyright_label.setWordWrap(True)
        author_layout.addWidget(copyright_label)
        
        author_label = QLabel("作者: Lin, X")
        author_label.setFont(QFont("Segoe UI", 8))
        author_label.setStyleSheet("color: #0066cc;")
        author_label.setAlignment(Qt.AlignCenter)
        author_label.setWordWrap(True)
        author_layout.addWidget(author_label)
        
        sidebar_layout.addWidget(author_frame)
        
        self.content = QStackedWidget()
        self.content.setStyleSheet("background-color: #ffffff;")
        
        self.init_page = QWidget()
        self.init_page.setStyleSheet("background-color: #ffffff;")
        init_layout = QVBoxLayout(self.init_page)
        init_layout.addStretch()
        
        welcome = QLabel("欢迎使用多模态数据科学工具箱")
        welcome.setFont(QFont("Segoe UI", 18, QFont.Bold))
        welcome.setStyleSheet("color: #0059b3; padding: 15px;")
        welcome.setAlignment(Qt.AlignCenter)
        init_layout.addWidget(welcome)
        
        hint = QLabel("请从侧边栏选择功能模块")
        hint.setFont(QFont("Segoe UI", 10))
        hint.setStyleSheet("color: #3399ff; padding: 15px;")
        hint.setAlignment(Qt.AlignCenter)
        init_layout.addWidget(hint)
        
        if os.path.exists("./icons/CASC-LOGO-transparency.png"):
            icon_label = QLabel()
            icon_pixmap = QPixmap("./icons/CASC-LOGO-transparency.png").scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            icon_label.setPixmap(icon_pixmap)
            icon_label.setAlignment(Qt.AlignCenter)
            init_layout.addWidget(icon_label)
        
        init_layout.addStretch()
        
        self.select_page = QWidget()
        self.select_page.setStyleSheet("background-color: #ffffff;")
        self.generate_page = QWidget()
        self.generate_page.setStyleSheet("background-color: #ffffff;")
        self.refine_page = QWidget()
        self.refine_page.setStyleSheet("background-color: #ffffff;")
        
        self.select_page.setStyleSheet("border: 1px solid #cce6ff; border-radius: 10px; background-color: #ffffff;")
        self.generate_page.setStyleSheet("border: 1px solid #cce6ff; border-radius: 10px; background-color: #ffffff;")
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
    
    def show_api_dialog(self):
        dialog = APIDialog(self)
        dialog.url_edit.setText(self.api_url)
        dialog.key_edit.setText(self.api_key)
        if dialog.exec_():
            self.api_url, self.api_key = dialog.get_values()
            if self.data_refine_window:
                self.data_refine_window.vlm_api_url = self.api_url
                self.data_refine_window.api_key = self.api_key
            if self.data_generate_window:
                # 更新数据制备的API设置
                pass
    
    def show_help(self):
        help_text = """图像文本标注工具使用说明 v2.0.5
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
   多模态（图像-文本）标注查验工具 v2.0.5
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
