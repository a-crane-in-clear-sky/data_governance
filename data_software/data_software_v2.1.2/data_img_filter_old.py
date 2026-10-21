import os
import os.path as osp
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

# ============= 功能函数 =============
def extract_features(image_paths, features_npy_path, model, preprocess, device, batch_size=32):
    """提取图像特征"""
    if osp.exists(features_npy_path):
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
            if len(imgs) == 0:
                continue
                
            imgs = torch.stack(imgs).to(device)
            feats = model.encode_image(imgs)
            feats = feats.cpu().numpy()
            features.append(feats)
            
    features = np.vstack(features)
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
        osp.join(img_dir, fname) 
        for fname in os.listdir(img_dir) 
        if fname.lower().endswith(allowed_extensions)
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
    features = normalize(features)
    
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

# ============= 主程序入口 =============
if __name__ == '__main__':
    # ===== 参数配置 (用户可根据需要修改) =====
    params = {
        'img_dir': '../目标检测数据集/tif/',         # 原始图像目录
        'json_dir': '../目标检测数据集/json/',       # 原始JSON目录
        'target_img_dir': '../target_img/',             # 目标图像输出目录
        'target_json_dir': '../target_json/',       # 目标JSON输出目录
        'features_npy_path': '../features.npy',             # 特征文件保存路径
        'allowed_extensions': ('.jpg', '.png', '.jpeg', '.bmp', '.tif', '.tiff'),  # 支持的文件格式
        'dbscan_params': {                         # DBSCAN聚类参数
            'eps': 0.35,
            'min_samples': 2,
            'metric': 'euclidean',
            'n_jobs': -1
        },
        'clip_model': "ViT-B/32",                 # CLIP模型版本
        'clip_model_dir': "./clip_model_dir/",
        'batch_size': 32                          # 批处理大小
    }
    
    # ===== 执行主处理函数 =====
    cluster_and_select_images(**params)
