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

NPY_DEFUALT_PATH = "../features.npy"
device = "cuda" if torch.cuda.is_available() else "cpu"
model, preprocess = clip.load("ViT-B/32", device=device)

def extract_features(image_paths, batch_size=32):
    if osp.exists(NPY_DEFUALT_PATH):
        return np.load(NPY_DEFUALT_PATH)
    features = []
    print(image_paths)
    model.eval()
    with torch.no_grad():
        print("extrating vit features:")
        for i in tqdm(range(0, len(image_paths), batch_size)):
            if i+batch_size >= len(image_paths):
                batch_paths = image_paths[i:len(image_paths)]
            else:
                batch_paths = image_paths[i:i+batch_size]
            imgs = []
            for path in batch_paths:
                try:
                    img = Image.open(path).convert('RGB')
                    img = preprocess(img)
                    imgs.append(img)
                except:
                    continue
            if len(imgs) == 0:
                continue
            imgs = torch.stack(imgs).to(device)
            feats = model.encode_image(imgs)
            feats = feats.cpu().numpy()
            features.append(feats)
    features = np.vstack(features)
    np.save(NPY_DEFUALT_PATH, features)
    return features
# img_dir = '/data/lzy/VisRAG/datasets--openbmb--VisRAG-Ret-Train-In-domain-data/output_images'
img_dir = '../目标检测数据集/tif'
# image_paths = [os.path.join(img_dir, fname) for fname in os.listdir(img_dir) if fname.lower().endswith(('.jpg', '.png', '.jpeg', '.tif', '.tiff'))]
image_paths = [os.path.join(img_dir, fname) for fname in os.listdir(img_dir)]
features = extract_features(image_paths)
from sklearn.preprocessing import normalize
features = normalize(features)
np.random.seed(42)
dbscan = DBSCAN(eps=0.35, min_samples=2, metric='euclidean', n_jobs=-1) #eps设置大小一点则会很相似才聚类在一起。min_samples表示每个聚类至少有两个样本，否则就会变成outliner
labels = dbscan.fit_predict(features)

# print(len(labels))

from collections import defaultdict

clusters = defaultdict(list)
clusters_idx = defaultdict(list)
max_label = max([l for l in labels if l >= 0], default=-1)
# print(62, max_label)
new_label = max_label + 1  # 最大max以后的都是outliner ，不用去重

for idx, label in enumerate(labels):
    if label == -1:
        clusters[new_label].append(image_paths[idx])
        clusters_idx[new_label].append(idx)
        new_label += 1
    else:
        clusters[label].append(image_paths[idx]) #这里面的label都是小于max_label的，大部分都相似，随机选一张就行？
        clusters_idx[label].append(idx)

selected = []
for label in clusters_idx:
    indices = clusters_idx[label]
    if label < max_label:        
        X = features[indices]
        cnt = X.shape[0]
        scale = cnt**-1
        feature_label = scale * np.sum(X, axis=0)
        # clusters_feature.append(feature_label)
        distances = np.linalg.norm(X - feature_label, axis=1)  # 计算每行的L2距离
        min_index = np.argmin(distances)  # 最小距离的索引
        # idx_sel = indices[min_index]
        # print(89, label, len(clusters[label]), len(indices), idx_sel, distances.shape)
        selected.append(clusters[label][min_index])
    else:
        selected.append(clusters[label][0])
# print(92, len(selected))

copy_specific_files(source_dir='../目标检测数据集/tif', target_dir='../target', source_json_dir='../目标检测数据集/json', target_json_dir='../target_json', file_names=selected)
# clusters_feature = np.array(clusters_feature, dtype=np.float32)

# print(70, clusters_feature.shape)

# 商业客机
# for cluster_id, img_list in clusters.items():
#     print(f"Cluster {cluster_id}:")
#     for img in img_list:
#         print(f"  {img}")
#     print('-'*30)
# SemDedup
