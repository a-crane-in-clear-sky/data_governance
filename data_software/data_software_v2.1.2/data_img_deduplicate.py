import os
import torch
from torchvision import models, transforms
from PIL import Image
from tqdm import tqdm
import numpy as np
import clip
from sklearn.cluster import DBSCAN
from copy_imgs import copy_specific_files
from sklearn.preprocessing import normalize
from collections import defaultdict
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QGroupBox, QFileDialog, QTextEdit, QProgressBar
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont


def extract_features(image_paths, features_npy_path, model, preprocess, device, batch_size=32):
    """提取图像特征"""
    if os.path.exists(features_npy_path):
        return np.load(features_npy_path)
    
    features = []
    model.eval()
    with torch.no_grad():
        print("Extracting ViT features:")
        for i in tqdm(range(0, len(image_paths), batch_size)):
            batch_end = min(i + batch_size, len(image_paths))
            batch_paths = image_paths[i:batch_end]
            
            imgs = []
            for path in batch_paths:
                try:
                    img = Image.open(path).convert('RGB')
                    img = preprocess(img)
                    imgs.append(img)
                except Exception as e:
                    print(f"Skipping {path} due to error: {e}")
                    continue
            if not imgs:
                continue
                
            imgs = torch.stack(imgs).to(device)
            feats = model.encode_image(imgs)
            feats = feats.cpu().numpy()
            features.append(feats)
            
    features = np.vstack(features) if features else np.array([])
    np.save(features_npy_path, features)
    return features


def cluster_and_select_images(
    img_dir,
    json_dir,
    target_img_dir,
    target_json_dir,
    features_npy_path,
    allowed_extensions,
    dbscan_params,
    clip_model="ViT-B/32",
    clip_model_dir="./clip_model_dir/",
    batch_size=32
):
    """主处理函数：聚类并选择代表性图像"""
    # 设备配置
    device = "cuda" if torch.cuda.is_available() else "cpu"
    
    # 加载模型
    model, preprocess = clip.load(
        clip_model, 
        device=device, 
        download_root=clip_model_dir
    )
    
    # 获取图像路径列表
    image_paths = [
        os.path.join(img_dir, fname) 
        for fname in os.listdir(img_dir) 
        if any(fname.lower().endswith(ext) for ext in allowed_extensions)
    ]
    
    if not image_paths:
        print(f"No images found in {img_dir} with extensions {allowed_extensions}")
        return
    
    print(f"Found {len(image_paths)} images for processing")
    
    # 特征提取
    features = extract_features(
        image_paths=image_paths,
        features_npy_path=features_npy_path,
        model=model,
        preprocess=preprocess,
        device=device,
        batch_size=batch_size
    )
    
    # 特征归一化
    features = normalize(features) if features.size > 0 else features
    
    # 聚类分析
    dbscan = DBSCAN(**dbscan_params)
    labels = dbscan.fit_predict(features)
    
    # 聚类结果处理
    clusters = defaultdict(list)
    clusters_idx = defaultdict(list)
    max_label = max([l for l in labels if l >= 0], default=-1)
    new_label = max_label + 1
    
    for idx, label in enumerate(labels):
        if label == -1:
            clusters[new_label].append(image_paths[idx])
            clusters_idx[new_label].append(idx)
            new_label += 1
        else:
            clusters[label].append(image_paths[idx])
            clusters_idx[label].append(idx)
    
    num_clusters = len(clusters)
    num_outliers = new_label - max_label - 1
    print(f"Found {num_clusters} clusters (including {num_outliers} outlier groups)")
    
    # 选择代表性图像
    selected = []
    for label in clusters_idx:
        indices = clusters_idx[label]
        if label < max_label:        
            X = features[indices]
            cnt = X.shape[0]
            scale = cnt**-1
            feature_label = scale * np.sum(X, axis=0)
            distances = np.linalg.norm(X - feature_label, axis=1)
            min_index = np.argmin(distances)
            selected.append(clusters[label][min_index])
        else:
            selected.append(clusters[label][0])
    
    print(f"Selected {len(selected)} representative images")
    
    # 复制选中的图像和对应JSON文件
    copy_specific_files(
        source_dir=img_dir,
        target_dir=target_img_dir,
        source_json_dir=json_dir,
        target_json_dir=target_json_dir,
        file_names=selected
    )
    
    print("Processing completed successfully!")


class ImageDeduplicator(QWidget):
    """图像去重算法界面"""
    def __init__(self, clip_model="ViT-B/32", model_dir="./clip_model_dir/", parent=None):
        super().__init__(parent)
        self.clip_model = clip_model
        self.model_dir = model_dir

        # 显式定义所有编辑框属性
        self.img_dir_edit = None
        self.json_dir_edit = None
        self.target_img_dir_edit = None
        self.target_json_dir_edit = None
        self.clip_model_edit = None
        self.model_dir_edit = None
        self.eps_edit = None
        self.min_samples_edit = None
        self.batch_size_edit = None
        self.ext_edit = None

        self.setup_ui()
    
    def setup_ui(self):
        """设置界面布局"""
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignTop)
        self.setMinimumHeight(800)
        
        # 标题
        title_label = QLabel("图像去重（算法）")
        title_label.setFont(QFont("Segoe UI", 14, QFont.Bold))
        title_label.setStyleSheet("color: #0059b3; margin-bottom: 15px;")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # 输入输出目录设置
        io_group = QGroupBox("输入输出目录")
        io_layout = QVBoxLayout(io_group)
        io_group.setMinimumHeight(180)
        
        # 图像目录 - 显式创建属性
        img_layout = QHBoxLayout()
        img_layout.addWidget(QLabel("原始图像目录:"))
        self.img_dir_edit = QLineEdit()
        self.img_dir_edit.setPlaceholderText("请选择包含原始图像的目录")
        img_layout.addWidget(self.img_dir_edit)
        img_browse_btn = QPushButton("浏览...")
        img_browse_btn.clicked.connect(lambda: self.browse_directory(self.img_dir_edit))
        img_layout.addWidget(img_browse_btn)
        io_layout.addLayout(img_layout)
        
        # JSON目录 - 显式创建属性
        json_layout = QHBoxLayout()
        json_layout.addWidget(QLabel("原始JSON目录:"))
        self.json_dir_edit = QLineEdit()
        self.json_dir_edit.setPlaceholderText("请选择包含原始JSON文件的目录")
        json_layout.addWidget(self.json_dir_edit)
        json_browse_btn = QPushButton("浏览...")
        json_browse_btn.clicked.connect(lambda: self.browse_directory(self.json_dir_edit))
        json_layout.addWidget(json_browse_btn)
        io_layout.addLayout(json_layout)
        
        # 目标图像目录 - 显式创建属性
        target_img_layout = QHBoxLayout()
        target_img_layout.addWidget(QLabel("去重后图像目录:"))
        self.target_img_dir_edit = QLineEdit()
        self.target_img_dir_edit.setPlaceholderText("请选择去重后图像输出目录")
        target_img_layout.addWidget(self.target_img_dir_edit)
        target_img_browse_btn = QPushButton("浏览...")
        target_img_browse_btn.clicked.connect(lambda: self.browse_directory(self.target_img_dir_edit))
        target_img_layout.addWidget(target_img_browse_btn)
        io_layout.addLayout(target_img_layout)
        
        # 目标JSON目录 - 显式创建属性
        target_json_layout = QHBoxLayout()
        target_json_layout.addWidget(QLabel("去重后JSON目录:"))
        self.target_json_dir_edit = QLineEdit()
        self.target_json_dir_edit.setPlaceholderText("请选择去重后JSON输出目录")
        target_json_layout.addWidget(self.target_json_dir_edit)
        target_json_browse_btn = QPushButton("浏览...")
        target_json_browse_btn.clicked.connect(lambda: self.browse_directory(self.target_json_dir_edit))
        target_json_layout.addWidget(target_json_browse_btn)
        io_layout.addLayout(target_json_layout)
        
        layout.addWidget(io_group)
        
        # 模型设置
        model_group = QGroupBox("模型设置")
        model_layout = QVBoxLayout(model_group)
        model_group.setMinimumHeight(120)
        
        # 模型名称 - 显式创建属性
        model_name_layout = QHBoxLayout()
        model_name_layout.addWidget(QLabel("CLIP模型:"))
        self.clip_model_edit = QLineEdit(self.clip_model)
        model_name_layout.addWidget(self.clip_model_edit)
        model_layout.addLayout(model_name_layout)
        
        # 模型目录 - 显式创建属性
        model_dir_layout = QHBoxLayout()
        model_dir_layout.addWidget(QLabel("模型所在目录:"))
        self.model_dir_edit = QLineEdit(self.model_dir)
        model_dir_layout.addWidget(self.model_dir_edit)
        model_dir_browse_btn = QPushButton("浏览...")
        model_dir_browse_btn.clicked.connect(lambda: self.browse_directory(self.model_dir_edit))
        model_dir_layout.addWidget(model_dir_browse_btn)
        model_layout.addLayout(model_dir_layout)
        
        layout.addWidget(model_group)
        
        # 算法参数设置
        params_group = QGroupBox("算法参数")
        params_layout = QVBoxLayout(params_group)
        params_group.setMinimumHeight(180)
        
        # DBSCAN参数
        dbscan_layout = QHBoxLayout()
        
        # eps参数 - 显式创建属性
        eps_layout = QVBoxLayout()
        eps_layout.addWidget(QLabel("eps (距离阈值):"))
        self.eps_edit = QLineEdit("0.35")
        eps_layout.addWidget(self.eps_edit)
        dbscan_layout.addLayout(eps_layout)
        
        # min_samples参数 - 显式创建属性
        min_samples_layout = QVBoxLayout()
        min_samples_layout.addWidget(QLabel("min_samples (最小样本数):"))
        self.min_samples_edit = QLineEdit("2")
        min_samples_layout.addWidget(self.min_samples_edit)
        dbscan_layout.addLayout(min_samples_layout)
        
        params_layout.addLayout(dbscan_layout)
        
        # 批处理大小 - 显式创建属性
        batch_layout = QHBoxLayout()
        batch_layout.addWidget(QLabel("批处理大小:"))
        self.batch_size_edit = QLineEdit("32")
        batch_layout.addWidget(self.batch_size_edit)
        params_layout.addLayout(batch_layout)
        
        # 文件扩展名 - 显式创建属性
        ext_layout = QHBoxLayout()
        ext_layout.addWidget(QLabel("支持的文件格式:"))
        self.ext_edit = QLineEdit(".jpg, .png, .jpeg, .bmp, .tif, .tiff")
        ext_layout.addWidget(self.ext_edit)
        params_layout.addLayout(ext_layout)
        layout.addWidget(params_group)
        
        # 进度条和日志
        progress_group = QGroupBox("处理进度")
        progress_layout = QVBoxLayout(progress_group)
        progress_group.setMinimumHeight(120)
        
        # 进度条
        progress_layout.addWidget(QLabel("进度:"))
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedHeight(25)
        progress_layout.addWidget(self.progress_bar)
        
        # 日志区域
        progress_layout.addWidget(QLabel("日志:"))
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setPlaceholderText("处理日志将显示在这里...")
        self.log_text.setFixedHeight(60)
        progress_layout.addWidget(self.log_text)
        
        layout.addWidget(progress_group)
        
        # 操作按钮
        btn_layout = QHBoxLayout()
        
        self.start_btn = QPushButton("开始去重")
        self.start_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        self.start_btn.clicked.connect(self.start_processing)
        btn_layout.addWidget(self.start_btn)
        
        self.stop_btn = QPushButton("停止去重")
        self.stop_btn.setStyleSheet("background-color: #f44336; color: white; font-weight: bold;")
        self.stop_btn.clicked.connect(self.stop_processing)
        self.stop_btn.setEnabled(False)
        btn_layout.addWidget(self.stop_btn)
        
        layout.addLayout(btn_layout)
    
    def create_path_layout(self, label_text, line_edit, placeholder, browse=True):
        """创建路径选择布局"""
        layout = QHBoxLayout()
        layout.addWidget(QLabel(label_text))
        setattr(self, line_edit, QLineEdit())
        getattr(self, line_edit).setPlaceholderText(placeholder)
        layout.addWidget(getattr(self, line_edit))
        
        if browse:
            browse_btn = QPushButton("浏览...")
            browse_btn.clicked.connect(lambda: self.browse_directory(getattr(self, line_edit)))
            layout.addWidget(browse_btn)
        
        return layout
    
    def create_setting_layout(self, label_text, line_edit, default_value):
        """创建参数设置布局"""
        layout = QHBoxLayout()
        layout.addWidget(QLabel(label_text))
        setattr(self, line_edit, QLineEdit(default_value))
        layout.addWidget(getattr(self, line_edit))
        return layout
    
    def browse_directory(self, line_edit):
        """浏览并选择目录"""
        dir_path = QFileDialog.getExistingDirectory(self, "选择目录")
        if dir_path:
            line_edit.setText(dir_path)
    
    def log_message(self, message):
        """记录日志消息"""
        self.log_text.append(message)
    
    def start_processing(self):
        """开始处理图像去重"""
        # 收集参数
        params = {
            'img_dir': self.img_dir_edit.text(),
            'json_dir': self.json_dir_edit.text(),
            'target_img_dir': self.target_img_dir_edit.text(),
            'target_json_dir': self.target_json_dir_edit.text(),
            'features_npy_path': './features.npy',
            'allowed_extensions': tuple(ext.strip() for ext in self.ext_edit.text().split(',')),
            'dbscan_params': {
                'eps': float(self.eps_edit.text()),
                'min_samples': int(self.min_samples_edit.text()),
                'metric': 'euclidean',
                'n_jobs': -1
            },
            'clip_model': self.clip_model_edit.text(),
            'clip_model_dir': self.model_dir_edit.text(),
            'batch_size': int(self.batch_size_edit.text())
        }
        
        # 验证参数
        for key in ['img_dir', 'json_dir', 'target_img_dir', 'target_json_dir']:
            if not params[key]:
                self.log_message(f"错误: {key.replace('_', ' ')}不能为空!")
                return
            if not os.path.exists(params[key]):
                self.log_message(f"错误: {key.replace('_', ' ')}不存在!")
                return
        
        # 创建处理线程
        self.processing_thread = ProcessingThread(params)
        self.processing_thread.log_signal.connect(self.log_message)
        self.processing_thread.progress_signal.connect(self.progress_bar.setValue)
        self.processing_thread.finished_signal.connect(self.on_processing_finished)
        
        # 更新按钮状态
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        
        # 启动线程
        self.log_message("开始图像去重处理...")
        self.processing_thread.start()
    
    def stop_processing(self):
        """停止处理过程"""
        if hasattr(self, 'processing_thread') and self.processing_thread.isRunning():
            self.processing_thread.stop()
            self.log_message("处理已停止!")
            self.start_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)
    
    def on_processing_finished(self):
        """处理完成后的回调"""
        self.log_message("处理完成!")
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)


class ProcessingThread(QThread):
    """后台处理线程"""
    log_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(int)
    finished_signal = pyqtSignal()
    
    def __init__(self, params):
        super().__init__()
        self.params = params
        self._is_running = True
    
    def run(self):
        """执行处理任务"""
        try:
            # 执行去重算法
            cluster_and_select_images(**self.params)
            self.log_signal.emit("图像去重处理完成!")
        except Exception as e:
            self.log_signal.emit(f"处理错误: {str(e)}")
        finally:
            self.finished_signal.emit()
    
    def stop(self):
        """停止线程"""
        self._is_running = False


if __name__ == '__main__':
    # 参数配置
    params = {
        'img_dir': '../目标检测数据集/tif/',
        'json_dir': '../目标检测数据集/json/',
        'target_img_dir': '../target_img/',
        'target_json_dir': '../target_json/',
        'features_npy_path': '../features.npy',
        'allowed_extensions': ('.jpg', '.png', '.jpeg', '.bmp', '.tif', '.tiff'),
        'dbscan_params': {
            'eps': 0.35,
            'min_samples': 2,
            'metric': 'euclidean',
            'n_jobs': -1
        },
        'clip_model': "ViT-B/32",
        'clip_model_dir': "./clip_model_dir/",
        'batch_size': 32
    }
    
    # 执行主处理函数
    cluster_and_select_images(**params)
