"""
Advanced AI System for Object Detection
รองรับ Multi-model ensemble, Custom model training, Transfer learning, Active learning
"""

import os
import json
import time
import pickle
import numpy as np
import pandas as pd
import sqlite3
import redis
import torch
import torch.nn as nn
import torch.optim as optim
import torchvision.transforms as transforms
import torchvision.models as models
from torch.utils.data import DataLoader, Dataset, random_split
import tensorflow as tf
from tensorflow import keras
from sklearn.ensemble import VotingClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from sklearn.model_selection import train_test_split
import cv2
import albumentations as A
from albumentations.pytorch import ToTensorV2
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum
import logging
import threading
import asyncio
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import multiprocessing as mp
from pathlib import Path
import shutil
import yaml
import wandb  # Weights & Biases for experiment tracking
from PIL import Image
import io
import base64
import hashlib
import uuid
from collections import defaultdict, deque
import statistics
import traceback
import warnings
warnings.filterwarnings('ignore')

# ตั้งค่า logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ModelType(Enum):
    """ประเภทของโมเดล"""
    YOLO = "yolo"
    FASTER_RCNN = "faster_rcnn"
    SSD = "ssd"
    EFFICIENTDET = "efficientdet"
    DETECTRON2 = "detectron2"
    CUSTOM_CNN = "custom_cnn"
    TRANSFORMER = "transformer"

class TrainingStrategy(Enum):
    """กลยุทธ์การฝึกโมเดล"""
    SCRATCH = "scratch"
    TRANSFER_LEARNING = "transfer_learning"
    FINE_TUNING = "fine_tuning"
    PROGRESSIVE_RESIZING = "progressive_resizing"
    KNOWLEDGE_DISTILLATION = "knowledge_distillation"

class EnsembleMethod(Enum):
    """วิธีการรวมโมเดล"""
    VOTING = "voting"
    WEIGHTED_AVERAGE = "weighted_average"
    STACKING = "stacking"
    BOOSTING = "boosting"
    BAYESIAN = "bayesian"

class ActiveLearningStrategy(Enum):
    """กลยุทธ์ Active Learning"""
    UNCERTAINTY_SAMPLING = "uncertainty_sampling"
    QUERY_BY_COMMITTEE = "query_by_committee"
    EXPECTED_MODEL_CHANGE = "expected_model_change"
    DIVERSITY_SAMPLING = "diversity_sampling"

@dataclass
class ModelConfig:
    """การกำหนดค่าโมเดล"""
    name: str
    model_type: ModelType
    architecture: str
    input_size: Tuple[int, int] = (640, 640)
    num_classes: int = 80
    pretrained: bool = True
    freeze_backbone: bool = False
    learning_rate: float = 0.001
    batch_size: int = 16
    epochs: int = 100
    weight_decay: float = 0.0005
    momentum: float = 0.9
    device: str = "cuda" if torch.cuda.is_available() else "cpu"
    mixed_precision: bool = True
    gradient_clipping: float = 1.0
    early_stopping_patience: int = 10
    save_best_only: bool = True
    
@dataclass
class TrainingConfig:
    """การกำหนดค่าการฝึก"""
    strategy: TrainingStrategy
    data_path: str
    output_path: str
    validation_split: float = 0.2
    test_split: float = 0.1
    augmentation_enabled: bool = True
    cross_validation_folds: int = 5
    hyperparameter_tuning: bool = True
    experiment_tracking: bool = True
    distributed_training: bool = False
    num_workers: int = 4
    pin_memory: bool = True
    
@dataclass
class EnsembleConfig:
    """การกำหนดค่า Ensemble"""
    method: EnsembleMethod
    models: List[str]
    weights: Optional[List[float]] = None
    voting_strategy: str = "soft"  # soft, hard
    confidence_threshold: float = 0.5
    nms_threshold: float = 0.4
    max_detections: int = 100
    
@dataclass
class ActiveLearningConfig:
    """การกำหนดค่า Active Learning"""
    strategy: ActiveLearningStrategy
    initial_labeled_size: int = 1000
    query_size: int = 100
    max_iterations: int = 10
    uncertainty_threshold: float = 0.8
    diversity_threshold: float = 0.7
    committee_size: int = 5
    
@dataclass
class ModelMetrics:
    """เมตริกของโมเดล"""
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    map_50: float  # mAP@0.5
    map_95: float  # mAP@0.5:0.95
    inference_time_ms: float
    model_size_mb: float
    flops: int
    params: int

class CustomDataset(Dataset):
    """Dataset สำหรับ Object Detection"""
    
    def __init__(self, data_path: str, annotations_file: str, 
                 transform=None, target_transform=None):
        self.data_path = Path(data_path)
        self.transform = transform
        self.target_transform = target_transform
        
        # โหลด annotations
        with open(annotations_file, 'r') as f:
            self.annotations = json.load(f)
        
        self.images = self.annotations['images']
        self.categories = self.annotations['categories']
        self.annotations_data = self.annotations['annotations']
        
        # สร้าง mapping
        self.image_id_to_annotations = defaultdict(list)
        for ann in self.annotations_data:
            self.image_id_to_annotations[ann['image_id']].append(ann)
    
    def __len__(self):
        return len(self.images)
    
    def __getitem__(self, idx):
        image_info = self.images[idx]
        image_path = self.data_path / image_info['file_name']
        
        # โหลดภาพ
        image = cv2.imread(str(image_path))
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # โหลด annotations
        annotations = self.image_id_to_annotations[image_info['id']]
        
        boxes = []
        labels = []
        for ann in annotations:
            bbox = ann['bbox']  # [x, y, width, height]
            # แปลงเป็น [x1, y1, x2, y2]
            x1, y1, w, h = bbox
            x2, y2 = x1 + w, y1 + h
            boxes.append([x1, y1, x2, y2])
            labels.append(ann['category_id'])
        
        target = {
            'boxes': torch.tensor(boxes, dtype=torch.float32),
            'labels': torch.tensor(labels, dtype=torch.int64),
            'image_id': torch.tensor(image_info['id'])
        }
        
        if self.transform:
            # Apply albumentations
            transformed = self.transform(image=image, bboxes=boxes, class_labels=labels)
            image = transformed['image']
            target['boxes'] = torch.tensor(transformed['bboxes'], dtype=torch.float32)
        
        return image, target

class ModelTrainer:
    """ระบบฝึกโมเดล"""
    
    def __init__(self, config: TrainingConfig):
        self.config = config
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.scaler = torch.cuda.amp.GradScaler() if config.mixed_precision else None
        
        # สร้างโฟลเดอร์ output
        Path(config.output_path).mkdir(parents=True, exist_ok=True)
        
        # เริ่มต้น experiment tracking
        if config.experiment_tracking:
            wandb.init(project="object-detection-advanced", config=asdict(config))
    
    def create_model(self, model_config: ModelConfig) -> nn.Module:
        """สร้างโมเดล"""
        if model_config.model_type == ModelType.FASTER_RCNN:
            return self._create_faster_rcnn(model_config)
        elif model_config.model_type == ModelType.YOLO:
            return self._create_yolo(model_config)
        elif model_config.model_type == ModelType.EFFICIENTDET:
            return self._create_efficientdet(model_config)
        elif model_config.model_type == ModelType.CUSTOM_CNN:
            return self._create_custom_cnn(model_config)
        else:
            raise ValueError(f"Unsupported model type: {model_config.model_type}")
    
    def _create_faster_rcnn(self, config: ModelConfig) -> nn.Module:
        """สร้าง Faster R-CNN"""
        from torchvision.models.detection import fasterrcnn_resnet50_fpn
        from torchvision.models.detection.faster_rcnn import FastRCNNPredictor
        
        model = fasterrcnn_resnet50_fpn(pretrained=config.pretrained)
        
        # แทนที่ classifier
        in_features = model.roi_heads.box_predictor.cls_score.in_features
        model.roi_heads.box_predictor = FastRCNNPredictor(in_features, config.num_classes)
        
        if config.freeze_backbone:
            for param in model.backbone.parameters():
                param.requires_grad = False
        
        return model
    
    def _create_yolo(self, config: ModelConfig) -> nn.Module:
        """สร้าง YOLO (ใช้ YOLOv5 architecture)"""
        # ตัวอย่างการสร้าง YOLO architecture
        class YOLOv5(nn.Module):
            def __init__(self, num_classes=80):
                super().__init__()
                self.backbone = models.efficientnet_b0(pretrained=True)
                self.backbone.classifier = nn.Identity()
                
                # YOLO head
                self.head = nn.Sequential(
                    nn.Conv2d(1280, 512, 3, padding=1),
                    nn.BatchNorm2d(512),
                    nn.ReLU(),
                    nn.Conv2d(512, 256, 3, padding=1),
                    nn.BatchNorm2d(256),
                    nn.ReLU(),
                    nn.Conv2d(256, (num_classes + 5) * 3, 1)  # 3 anchors per cell
                )
            
            def forward(self, x):
                features = self.backbone(x)
                features = features.view(features.size(0), -1, 1, 1)
                features = features.expand(-1, -1, 20, 20)  # Adjust size
                output = self.head(features)
                return output
        
        return YOLOv5(config.num_classes)
    
    def _create_efficientdet(self, config: ModelConfig) -> nn.Module:
        """สร้าง EfficientDet"""
        # ตัวอย่างการสร้าง EfficientDet architecture
        class EfficientDet(nn.Module):
            def __init__(self, num_classes=80):
                super().__init__()
                self.backbone = models.efficientnet_b0(pretrained=True)
                self.backbone.classifier = nn.Identity()
                
                # FPN
                self.fpn = nn.ModuleList([
                    nn.Conv2d(1280, 256, 1),
                    nn.Conv2d(256, 256, 3, padding=1),
                    nn.Conv2d(256, 256, 3, padding=1)
                ])
                
                # Detection head
                self.cls_head = nn.Conv2d(256, num_classes * 9, 3, padding=1)
                self.reg_head = nn.Conv2d(256, 4 * 9, 3, padding=1)
            
            def forward(self, x):
                features = self.backbone(x)
                # Simplified FPN and detection head
                cls_output = self.cls_head(features)
                reg_output = self.reg_head(features)
                return {'classification': cls_output, 'regression': reg_output}
        
        return EfficientDet(config.num_classes)
    
    def _create_custom_cnn(self, config: ModelConfig) -> nn.Module:
        """สร้าง Custom CNN"""
        class CustomCNN(nn.Module):
            def __init__(self, num_classes=80):
                super().__init__()
                self.features = nn.Sequential(
                    # Block 1
                    nn.Conv2d(3, 64, 3, padding=1),
                    nn.BatchNorm2d(64),
                    nn.ReLU(),
                    nn.Conv2d(64, 64, 3, padding=1),
                    nn.BatchNorm2d(64),
                    nn.ReLU(),
                    nn.MaxPool2d(2),
                    
                    # Block 2
                    nn.Conv2d(64, 128, 3, padding=1),
                    nn.BatchNorm2d(128),
                    nn.ReLU(),
                    nn.Conv2d(128, 128, 3, padding=1),
                    nn.BatchNorm2d(128),
                    nn.ReLU(),
                    nn.MaxPool2d(2),
                    
                    # Block 3
                    nn.Conv2d(128, 256, 3, padding=1),
                    nn.BatchNorm2d(256),
                    nn.ReLU(),
                    nn.Conv2d(256, 256, 3, padding=1),
                    nn.BatchNorm2d(256),
                    nn.ReLU(),
                    nn.MaxPool2d(2),
                    
                    # Block 4
                    nn.Conv2d(256, 512, 3, padding=1),
                    nn.BatchNorm2d(512),
                    nn.ReLU(),
                    nn.Conv2d(512, 512, 3, padding=1),
                    nn.BatchNorm2d(512),
                    nn.ReLU(),
                    nn.MaxPool2d(2),
                )
                
                self.classifier = nn.Sequential(
                    nn.AdaptiveAvgPool2d((7, 7)),
                    nn.Flatten(),
                    nn.Linear(512 * 7 * 7, 4096),
                    nn.ReLU(),
                    nn.Dropout(0.5),
                    nn.Linear(4096, 1000),
                    nn.ReLU(),
                    nn.Dropout(0.5),
                    nn.Linear(1000, num_classes)
                )
            
            def forward(self, x):
                x = self.features(x)
                x = self.classifier(x)
                return x
        
        return CustomCNN(config.num_classes)
    
    def create_data_loaders(self, dataset_path: str, annotations_file: str,
                           batch_size: int = 16) -> Tuple[DataLoader, DataLoader, DataLoader]:
        """สร้าง data loaders"""
        
        # Data augmentation
        train_transform = A.Compose([
            A.Resize(640, 640),
            A.HorizontalFlip(p=0.5),
            A.VerticalFlip(p=0.2),
            A.RandomRotate90(p=0.2),
            A.RandomBrightnessContrast(p=0.3),
            A.HueSaturationValue(p=0.3),
            A.GaussNoise(p=0.2),
            A.MotionBlur(p=0.2),
            A.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
            ToTensorV2()
        ], bbox_params=A.BboxParams(format='pascal_voc', label_fields=['class_labels']))
        
        val_transform = A.Compose([
            A.Resize(640, 640),
            A.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
            ToTensorV2()
        ], bbox_params=A.BboxParams(format='pascal_voc', label_fields=['class_labels']))
        
        # สร้าง dataset
        full_dataset = CustomDataset(dataset_path, annotations_file)
        
        # แบ่งข้อมูล
        total_size = len(full_dataset)
        train_size = int(total_size * (1 - self.config.validation_split - self.config.test_split))
        val_size = int(total_size * self.config.validation_split)
        test_size = total_size - train_size - val_size
        
        train_dataset, val_dataset, test_dataset = random_split(
            full_dataset, [train_size, val_size, test_size]
        )
        
        # Apply transforms
        train_dataset.dataset.transform = train_transform
        val_dataset.dataset.transform = val_transform
        test_dataset.dataset.transform = val_transform
        
        # สร้าง data loaders
        train_loader = DataLoader(
            train_dataset, batch_size=batch_size, shuffle=True,
            num_workers=self.config.num_workers, pin_memory=self.config.pin_memory,
            collate_fn=self._collate_fn
        )
        
        val_loader = DataLoader(
            val_dataset, batch_size=batch_size, shuffle=False,
            num_workers=self.config.num_workers, pin_memory=self.config.pin_memory,
            collate_fn=self._collate_fn
        )
        
        test_loader = DataLoader(
            test_dataset, batch_size=batch_size, shuffle=False,
            num_workers=self.config.num_workers, pin_memory=self.config.pin_memory,
            collate_fn=self._collate_fn
        )
        
        return train_loader, val_loader, test_loader
    
    def _collate_fn(self, batch):
        """Custom collate function for object detection"""
        images, targets = zip(*batch)
        images = torch.stack(images)
        return images, list(targets)
    
    def train_model(self, model: nn.Module, train_loader: DataLoader,
                   val_loader: DataLoader, model_config: ModelConfig) -> Dict[str, Any]:
        """ฝึกโมเดล"""
        
        model = model.to(self.device)
        
        # Optimizer และ scheduler
        optimizer = optim.AdamW(
            model.parameters(),
            lr=model_config.learning_rate,
            weight_decay=model_config.weight_decay
        )
        
        scheduler = optim.lr_scheduler.CosineAnnealingLR(
            optimizer, T_max=model_config.epochs
        )
        
        # Loss function
        criterion = nn.CrossEntropyLoss()
        
        # Training loop
        best_val_loss = float('inf')
        patience_counter = 0
        train_losses = []
        val_losses = []
        
        for epoch in range(model_config.epochs):
            # Training phase
            model.train()
            train_loss = 0.0
            train_correct = 0
            train_total = 0
            
            for batch_idx, (images, targets) in enumerate(train_loader):
                images = images.to(self.device)
                
                # Forward pass
                if model_config.mixed_precision and self.scaler:
                    with torch.cuda.amp.autocast():
                        outputs = model(images)
                        # Simplified loss calculation for demonstration
                        loss = criterion(outputs, torch.randint(0, model_config.num_classes, (images.size(0),)).to(self.device))
                    
                    # Backward pass
                    optimizer.zero_grad()
                    self.scaler.scale(loss).backward()
                    
                    if model_config.gradient_clipping > 0:
                        self.scaler.unscale_(optimizer)
                        torch.nn.utils.clip_grad_norm_(model.parameters(), model_config.gradient_clipping)
                    
                    self.scaler.step(optimizer)
                    self.scaler.update()
                else:
                    outputs = model(images)
                    loss = criterion(outputs, torch.randint(0, model_config.num_classes, (images.size(0),)).to(self.device))
                    
                    optimizer.zero_grad()
                    loss.backward()
                    
                    if model_config.gradient_clipping > 0:
                        torch.nn.utils.clip_grad_norm_(model.parameters(), model_config.gradient_clipping)
                    
                    optimizer.step()
                
                train_loss += loss.item()
                
                # Calculate accuracy (simplified)
                _, predicted = torch.max(outputs.data, 1)
                train_total += images.size(0)
                train_correct += predicted.eq(torch.randint(0, model_config.num_classes, (images.size(0),)).to(self.device)).sum().item()
                
                if batch_idx % 100 == 0:
                    logger.info(f'Epoch {epoch}, Batch {batch_idx}, Loss: {loss.item():.4f}')
            
            # Validation phase
            model.eval()
            val_loss = 0.0
            val_correct = 0
            val_total = 0
            
            with torch.no_grad():
                for images, targets in val_loader:
                    images = images.to(self.device)
                    outputs = model(images)
                    loss = criterion(outputs, torch.randint(0, model_config.num_classes, (images.size(0),)).to(self.device))
                    
                    val_loss += loss.item()
                    _, predicted = torch.max(outputs.data, 1)
                    val_total += images.size(0)
                    val_correct += predicted.eq(torch.randint(0, model_config.num_classes, (images.size(0),)).to(self.device)).sum().item()
            
            # Calculate metrics
            train_loss /= len(train_loader)
            val_loss /= len(val_loader)
            train_acc = 100. * train_correct / train_total
            val_acc = 100. * val_correct / val_total
            
            train_losses.append(train_loss)
            val_losses.append(val_loss)
            
            logger.info(f'Epoch {epoch}: Train Loss: {train_loss:.4f}, Train Acc: {train_acc:.2f}%, '
                       f'Val Loss: {val_loss:.4f}, Val Acc: {val_acc:.2f}%')
            
            # Log to wandb
            if self.config.experiment_tracking:
                wandb.log({
                    'epoch': epoch,
                    'train_loss': train_loss,
                    'val_loss': val_loss,
                    'train_acc': train_acc,
                    'val_acc': val_acc,
                    'learning_rate': optimizer.param_groups[0]['lr']
                })
            
            # Early stopping
            if val_loss < best_val_loss:
                best_val_loss = val_loss
                patience_counter = 0
                
                if model_config.save_best_only:
                    torch.save({
                        'epoch': epoch,
                        'model_state_dict': model.state_dict(),
                        'optimizer_state_dict': optimizer.state_dict(),
                        'val_loss': val_loss,
                        'config': asdict(model_config)
                    }, os.path.join(self.config.output_path, f'{model_config.name}_best.pth'))
            else:
                patience_counter += 1
                
                if patience_counter >= model_config.early_stopping_patience:
                    logger.info(f'Early stopping at epoch {epoch}')
                    break
            
            scheduler.step()
        
        return {
            'train_losses': train_losses,
            'val_losses': val_losses,
            'best_val_loss': best_val_loss,
            'final_epoch': epoch
        }
    
    def transfer_learning(self, source_model_path: str, target_config: ModelConfig,
                         train_loader: DataLoader, val_loader: DataLoader) -> nn.Module:
        """Transfer Learning"""
        
        # โหลด pre-trained model
        checkpoint = torch.load(source_model_path, map_location=self.device)
        source_model = self.create_model(target_config)
        source_model.load_state_dict(checkpoint['model_state_dict'])
        
        # Freeze early layers
        if target_config.freeze_backbone:
            for name, param in source_model.named_parameters():
                if 'classifier' not in name and 'head' not in name:
                    param.requires_grad = False
        
        # Replace final layer for new task
        if hasattr(source_model, 'classifier'):
            in_features = source_model.classifier[-1].in_features
            source_model.classifier[-1] = nn.Linear(in_features, target_config.num_classes)
        elif hasattr(source_model, 'head'):
            in_features = source_model.head[-1].in_features
            source_model.head[-1] = nn.Linear(in_features, target_config.num_classes)
        
        # Fine-tune
        self.train_model(source_model, train_loader, val_loader, target_config)
        
        return source_model
    
    def knowledge_distillation(self, teacher_model: nn.Module, student_config: ModelConfig,
                              train_loader: DataLoader, val_loader: DataLoader,
                              temperature: float = 3.0, alpha: float = 0.7) -> nn.Module:
        """Knowledge Distillation"""
        
        student_model = self.create_model(student_config).to(self.device)
        teacher_model = teacher_model.to(self.device)
        teacher_model.eval()
        
        optimizer = optim.AdamW(
            student_model.parameters(),
            lr=student_config.learning_rate,
            weight_decay=student_config.weight_decay
        )
        
        def distillation_loss(student_outputs, teacher_outputs, targets, temperature, alpha):
            # Soft targets from teacher
            soft_targets = torch.softmax(teacher_outputs / temperature, dim=1)
            soft_student = torch.log_softmax(student_outputs / temperature, dim=1)
            soft_loss = -torch.sum(soft_targets * soft_student) / student_outputs.size(0)
            
            # Hard targets
            hard_loss = nn.CrossEntropyLoss()(student_outputs, targets)
            
            return alpha * soft_loss * (temperature ** 2) + (1 - alpha) * hard_loss
        
        for epoch in range(student_config.epochs):
            student_model.train()
            total_loss = 0.0
            
            for images, targets in train_loader:
                images = images.to(self.device)
                
                # Teacher predictions
                with torch.no_grad():
                    teacher_outputs = teacher_model(images)
                
                # Student predictions
                student_outputs = student_model(images)
                
                # Calculate distillation loss
                loss = distillation_loss(
                    student_outputs, teacher_outputs,
                    torch.randint(0, student_config.num_classes, (images.size(0),)).to(self.device),
                    temperature, alpha
                )
                
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()
                
                total_loss += loss.item()
            
            logger.info(f'Distillation Epoch {epoch}: Loss: {total_loss/len(train_loader):.4f}')
        
        return student_model

class EnsembleManager:
    """จัดการ Model Ensemble"""
    
    def __init__(self, config: EnsembleConfig):
        self.config = config
        self.models = {}
        self.model_weights = config.weights or [1.0] * len(config.models)
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    
    def load_models(self, model_paths: Dict[str, str]):
        """โหลดโมเดลทั้งหมด"""
        for model_name, model_path in model_paths.items():
            if model_name in self.config.models:
                checkpoint = torch.load(model_path, map_location=self.device)
                
                # สร้างโมเดลตาม config
                model_config = ModelConfig(
                    name=model_name,
                    model_type=ModelType(checkpoint['config']['model_type']),
                    architecture=checkpoint['config']['architecture'],
                    num_classes=checkpoint['config']['num_classes']
                )
                
                trainer = ModelTrainer(TrainingConfig(
                    strategy=TrainingStrategy.SCRATCH,
                    data_path="",
                    output_path=""
                ))
                
                model = trainer.create_model(model_config)
                model.load_state_dict(checkpoint['model_state_dict'])
                model.to(self.device)
                model.eval()
                
                self.models[model_name] = model
                logger.info(f"Loaded model: {model_name}")
    
    def predict_ensemble(self, images: torch.Tensor) -> Dict[str, Any]:
        """ทำนายด้วย ensemble"""
        images = images.to(self.device)
        
        if self.config.method == EnsembleMethod.VOTING:
            return self._voting_prediction(images)
        elif self.config.method == EnsembleMethod.WEIGHTED_AVERAGE:
            return self._weighted_average_prediction(images)
        elif self.config.method == EnsembleMethod.STACKING:
            return self._stacking_prediction(images)
        else:
            raise ValueError(f"Unsupported ensemble method: {self.config.method}")
    
    def _voting_prediction(self, images: torch.Tensor) -> Dict[str, Any]:
        """Voting ensemble"""
        all_predictions = []
        
        with torch.no_grad():
            for model_name, model in self.models.items():
                predictions = model(images)
                
                if self.config.voting_strategy == "soft":
                    predictions = torch.softmax(predictions, dim=1)
                else:  # hard voting
                    predictions = torch.argmax(predictions, dim=1)
                
                all_predictions.append(predictions)
        
        if self.config.voting_strategy == "soft":
            # Average probabilities
            ensemble_pred = torch.stack(all_predictions).mean(dim=0)
            final_pred = torch.argmax(ensemble_pred, dim=1)
            confidence = torch.max(ensemble_pred, dim=1)[0]
        else:
            # Majority voting
            all_predictions = torch.stack(all_predictions)
            final_pred = torch.mode(all_predictions, dim=0)[0]
            confidence = torch.ones_like(final_pred, dtype=torch.float32)
        
        return {
            'predictions': final_pred,
            'confidence': confidence,
            'individual_predictions': all_predictions
        }
    
    def _weighted_average_prediction(self, images: torch.Tensor) -> Dict[str, Any]:
        """Weighted average ensemble"""
        weighted_predictions = []
        
        with torch.no_grad():
            for i, (model_name, model) in enumerate(self.models.items()):
                predictions = model(images)
                predictions = torch.softmax(predictions, dim=1)
                
                weight = self.model_weights[i]
                weighted_predictions.append(predictions * weight)
        
        # Weighted average
        ensemble_pred = torch.stack(weighted_predictions).sum(dim=0)
        ensemble_pred = ensemble_pred / sum(self.model_weights)
        
        final_pred = torch.argmax(ensemble_pred, dim=1)
        confidence = torch.max(ensemble_pred, dim=1)[0]
        
        return {
            'predictions': final_pred,
            'confidence': confidence,
            'ensemble_probabilities': ensemble_pred
        }
    
    def _stacking_prediction(self, images: torch.Tensor) -> Dict[str, Any]:
        """Stacking ensemble"""
        # Get predictions from all base models
        base_predictions = []
        
        with torch.no_grad():
            for model_name, model in self.models.items():
                predictions = model(images)
                predictions = torch.softmax(predictions, dim=1)
                base_predictions.append(predictions)
        
        # Stack predictions as features
        stacked_features = torch.cat(base_predictions, dim=1)
        
        # Meta-learner (simple linear layer for demonstration)
        if not hasattr(self, 'meta_learner'):
            input_size = stacked_features.size(1)
            output_size = base_predictions[0].size(1)
            self.meta_learner = nn.Linear(input_size, output_size).to(self.device)
        
        # Meta-learner prediction
        meta_pred = self.meta_learner(stacked_features)
        meta_pred = torch.softmax(meta_pred, dim=1)
        
        final_pred = torch.argmax(meta_pred, dim=1)
        confidence = torch.max(meta_pred, dim=1)[0]
        
        return {
            'predictions': final_pred,
            'confidence': confidence,
            'meta_probabilities': meta_pred,
            'base_predictions': base_predictions
        }
    
    def evaluate_ensemble(self, test_loader: DataLoader) -> Dict[str, float]:
        """ประเมิน ensemble performance"""
        all_predictions = []
        all_targets = []
        all_confidences = []
        
        with torch.no_grad():
            for images, targets in test_loader:
                result = self.predict_ensemble(images)
                
                all_predictions.extend(result['predictions'].cpu().numpy())
                all_confidences.extend(result['confidence'].cpu().numpy())
                # Simplified target extraction
                all_targets.extend([0] * len(images))  # Placeholder
        
        # Calculate metrics
        accuracy = accuracy_score(all_targets, all_predictions)
        precision = precision_score(all_targets, all_predictions, average='weighted', zero_division=0)
        recall = recall_score(all_targets, all_predictions, average='weighted', zero_division=0)
        f1 = f1_score(all_targets, all_predictions, average='weighted', zero_division=0)
        
        avg_confidence = np.mean(all_confidences)
        
        return {
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1_score': f1,
            'average_confidence': avg_confidence
        }

class ActiveLearningManager:
    """จัดการ Active Learning"""
    
    def __init__(self, config: ActiveLearningConfig):
        self.config = config
        self.labeled_pool = []
        self.unlabeled_pool = []
        self.query_history = []
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    
    def initialize_pools(self, dataset: Dataset, initial_labeled_indices: Optional[List[int]] = None):
        """เริ่มต้น labeled และ unlabeled pools"""
        total_size = len(dataset)
        
        if initial_labeled_indices is None:
            # Random sampling for initial labeled set
            indices = np.random.permutation(total_size)
            labeled_indices = indices[:self.config.initial_labeled_size]
            unlabeled_indices = indices[self.config.initial_labeled_size:]
        else:
            labeled_indices = initial_labeled_indices
            unlabeled_indices = [i for i in range(total_size) if i not in labeled_indices]
        
        self.labeled_pool = labeled_indices.tolist()
        self.unlabeled_pool = unlabeled_indices
        
        logger.info(f"Initialized pools: {len(self.labeled_pool)} labeled, {len(self.unlabeled_pool)} unlabeled")
    
    def query_samples(self, model: nn.Module, unlabeled_loader: DataLoader) -> List[int]:
        """เลือกตัวอย่างสำหรับ labeling"""
        
        if self.config.strategy == ActiveLearningStrategy.UNCERTAINTY_SAMPLING:
            return self._uncertainty_sampling(model, unlabeled_loader)
        elif self.config.strategy == ActiveLearningStrategy.QUERY_BY_COMMITTEE:
            return self._query_by_committee(model, unlabeled_loader)
        elif self.config.strategy == ActiveLearningStrategy.DIVERSITY_SAMPLING:
            return self._diversity_sampling(model, unlabeled_loader)
        else:
            raise ValueError(f"Unsupported active learning strategy: {self.config.strategy}")
    
    def _uncertainty_sampling(self, model: nn.Module, unlabeled_loader: DataLoader) -> List[int]:
        """Uncertainty sampling strategy"""
        model.eval()
        uncertainties = []
        indices = []
        
        with torch.no_grad():
            for batch_idx, (images, targets) in enumerate(unlabeled_loader):
                images = images.to(self.device)
                outputs = model(images)
                
                # Calculate uncertainty (entropy)
                probs = torch.softmax(outputs, dim=1)
                entropy = -torch.sum(probs * torch.log(probs + 1e-8), dim=1)
                
                uncertainties.extend(entropy.cpu().numpy())
                batch_indices = [self.unlabeled_pool[batch_idx * unlabeled_loader.batch_size + i] 
                               for i in range(len(images))]
                indices.extend(batch_indices)
        
        # Select samples with highest uncertainty
        uncertainty_indices = np.argsort(uncertainties)[-self.config.query_size:]
        selected_indices = [indices[i] for i in uncertainty_indices]
        
        return selected_indices
    
    def _query_by_committee(self, models: List[nn.Module], unlabeled_loader: DataLoader) -> List[int]:
        """Query by committee strategy"""
        disagreements = []
        indices = []
        
        with torch.no_grad():
            for batch_idx, (images, targets) in enumerate(unlabeled_loader):
                images = images.to(self.device)
                
                # Get predictions from all committee members
                committee_predictions = []
                for model in models:
                    model.eval()
                    outputs = model(images)
                    predictions = torch.argmax(outputs, dim=1)
                    committee_predictions.append(predictions)
                
                # Calculate disagreement
                committee_predictions = torch.stack(committee_predictions)
                
                for i in range(images.size(0)):
                    sample_predictions = committee_predictions[:, i]
                    unique_predictions = torch.unique(sample_predictions)
                    disagreement = len(unique_predictions) / len(models)
                    disagreements.append(disagreement)
                
                batch_indices = [self.unlabeled_pool[batch_idx * unlabeled_loader.batch_size + i] 
                               for i in range(len(images))]
                indices.extend(batch_indices)
        
        # Select samples with highest disagreement
        disagreement_indices = np.argsort(disagreements)[-self.config.query_size:]
        selected_indices = [indices[i] for i in disagreement_indices]
        
        return selected_indices
    
    def _diversity_sampling(self, model: nn.Module, unlabeled_loader: DataLoader) -> List[int]:
        """Diversity sampling strategy"""
        model.eval()
        features = []
        indices = []
        
        # Extract features
        with torch.no_grad():
            for batch_idx, (images, targets) in enumerate(unlabeled_loader):
                images = images.to(self.device)
                
                # Get intermediate features (before final layer)
                if hasattr(model, 'features'):
                    batch_features = model.features(images)
                else:
                    # Use penultimate layer
                    batch_features = model(images)
                
                batch_features = batch_features.view(batch_features.size(0), -1)
                features.extend(batch_features.cpu().numpy())
                
                batch_indices = [self.unlabeled_pool[batch_idx * unlabeled_loader.batch_size + i] 
                               for i in range(len(images))]
                indices.extend(batch_indices)
        
        features = np.array(features)
        
        # K-means clustering for diversity
        from sklearn.cluster import KMeans
        
        n_clusters = min(self.config.query_size, len(features))
        kmeans = KMeans(n_clusters=n_clusters, random_state=42)
        cluster_labels = kmeans.fit_predict(features)
        
        # Select one sample from each cluster (closest to centroid)
        selected_indices = []
        for cluster_id in range(n_clusters):
            cluster_mask = cluster_labels == cluster_id
            cluster_features = features[cluster_mask]
            cluster_indices = np.array(indices)[cluster_mask]
            
            if len(cluster_features) > 0:
                # Find closest to centroid
                centroid = kmeans.cluster_centers_[cluster_id]
                distances = np.linalg.norm(cluster_features - centroid, axis=1)
                closest_idx = np.argmin(distances)
                selected_indices.append(cluster_indices[closest_idx])
        
        return selected_indices[:self.config.query_size]
    
    def update_pools(self, queried_indices: List[int]):
        """อัปเดต pools หลังจาก labeling"""
        # Move queried samples from unlabeled to labeled pool
        for idx in queried_indices:
            if idx in self.unlabeled_pool:
                self.unlabeled_pool.remove(idx)
                self.labeled_pool.append(idx)
        
        self.query_history.append({
            'iteration': len(self.query_history),
            'queried_indices': queried_indices,
            'labeled_pool_size': len(self.labeled_pool),
            'unlabeled_pool_size': len(self.unlabeled_pool)
        })
        
        logger.info(f"Updated pools: {len(self.labeled_pool)} labeled, {len(self.unlabeled_pool)} unlabeled")
    
    def active_learning_loop(self, model: nn.Module, full_dataset: Dataset,
                           trainer: ModelTrainer, model_config: ModelConfig) -> Dict[str, Any]:
        """Active learning loop หลัก"""
        
        results = {
            'iterations': [],
            'labeled_sizes': [],
            'accuracies': [],
            'query_history': []
        }
        
        for iteration in range(self.config.max_iterations):
            logger.info(f"Active Learning Iteration {iteration + 1}")
            
            # Create current labeled dataset
            labeled_indices = self.labeled_pool
            labeled_dataset = torch.utils.data.Subset(full_dataset, labeled_indices)
            
            # Create data loader
            labeled_loader = DataLoader(
                labeled_dataset, batch_size=model_config.batch_size,
                shuffle=True, num_workers=4
            )
            
            # Train model on current labeled data
            trainer.train_model(model, labeled_loader, labeled_loader, model_config)
            
            # Evaluate model
            # (Simplified evaluation)
            accuracy = 0.85 + iteration * 0.02  # Placeholder
            
            results['iterations'].append(iteration)
            results['labeled_sizes'].append(len(self.labeled_pool))
            results['accuracies'].append(accuracy)
            
            # Query new samples
            if len(self.unlabeled_pool) > 0:
                unlabeled_indices = self.unlabeled_pool[:1000]  # Limit for efficiency
                unlabeled_dataset = torch.utils.data.Subset(full_dataset, unlabeled_indices)
                unlabeled_loader = DataLoader(
                    unlabeled_dataset, batch_size=model_config.batch_size,
                    shuffle=False, num_workers=4
                )
                
                queried_indices = self.query_samples(model, unlabeled_loader)
                self.update_pools(queried_indices)
                
                results['query_history'].append({
                    'iteration': iteration,
                    'queried_indices': queried_indices
                })
            
            logger.info(f"Iteration {iteration + 1}: Accuracy = {accuracy:.4f}, "
                       f"Labeled samples = {len(self.labeled_pool)}")
        
        return results

class AdvancedAISystem:
    """ระบบ AI ขั้นสูงหลัก"""
    
    def __init__(self, config_path: str = None):
        self.config = self._load_config(config_path) if config_path else self._default_config()
        self.trainer = ModelTrainer(self.config['training'])
        self.ensemble_manager = EnsembleManager(self.config['ensemble'])
        self.active_learning_manager = ActiveLearningManager(self.config['active_learning'])
        
        # Model registry
        self.model_registry = {}
        self.experiment_results = {}
        
        # Initialize database
        self.init_database()
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """โหลด config จากไฟล์"""
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    
    def _default_config(self) -> Dict[str, Any]:
        """Config เริ่มต้น"""
        return {
            'training': TrainingConfig(
                strategy=TrainingStrategy.TRANSFER_LEARNING,
                data_path="data/",
                output_path="models/",
                experiment_tracking=True
            ),
            'ensemble': EnsembleConfig(
                method=EnsembleMethod.WEIGHTED_AVERAGE,
                models=["model1", "model2", "model3"],
                weights=[0.4, 0.35, 0.25]
            ),
            'active_learning': ActiveLearningConfig(
                strategy=ActiveLearningStrategy.UNCERTAINTY_SAMPLING,
                initial_labeled_size=1000,
                query_size=100
            )
        }
    
    def init_database(self):
        """เริ่มต้นฐานข้อมูล"""
        try:
            conn = sqlite3.connect("advanced_ai.db")
            cursor = conn.cursor()
            
            # Models table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS models (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    model_type TEXT NOT NULL,
                    architecture TEXT,
                    config TEXT,
                    metrics TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    file_path TEXT
                )
            ''')
            
            # Experiments table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS experiments (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    experiment_type TEXT,
                    config TEXT,
                    results TEXT,
                    status TEXT DEFAULT 'running',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP
                )
            ''')
            
            # Active learning table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS active_learning_sessions (
                    id TEXT PRIMARY KEY,
                    model_id TEXT,
                    strategy TEXT,
                    iteration INTEGER,
                    labeled_size INTEGER,
                    accuracy REAL,
                    queried_samples TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Database initialization error: {e}")
    
    def register_model(self, model: nn.Module, model_config: ModelConfig,
                      metrics: ModelMetrics, file_path: str) -> str:
        """ลงทะเบียนโมเดล"""
        model_id = str(uuid.uuid4())
        
        try:
            conn = sqlite3.connect("advanced_ai.db")
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO models (id, name, model_type, architecture, config, metrics, file_path)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                model_id,
                model_config.name,
                model_config.model_type.value,
                model_config.architecture,
                json.dumps(asdict(model_config)),
                json.dumps(asdict(metrics)),
                file_path
            ))
            
            conn.commit()
            conn.close()
            
            self.model_registry[model_id] = {
                'model': model,
                'config': model_config,
                'metrics': metrics,
                'file_path': file_path
            }
            
            logger.info(f"Model registered: {model_config.name} (ID: {model_id})")
            return model_id
            
        except Exception as e:
            logger.error(f"Model registration error: {e}")
            return ""
    
    def train_multiple_models(self, model_configs: List[ModelConfig],
                             dataset_path: str, annotations_file: str) -> Dict[str, Any]:
        """ฝึกโมเดลหลายตัว"""
        
        results = {}
        
        # สร้าง data loaders
        train_loader, val_loader, test_loader = self.trainer.create_data_loaders(
            dataset_path, annotations_file
        )
        
        for model_config in model_configs:
            logger.info(f"Training model: {model_config.name}")
            
            try:
                # สร้างโมเดล
                model = self.trainer.create_model(model_config)
                
                # ฝึกโมเดล
                training_result = self.trainer.train_model(
                    model, train_loader, val_loader, model_config
                )
                
                # ประเมินโมเดล
                metrics = self._evaluate_model(model, test_loader, model_config)
                
                # บันทึกโมเดล
                model_path = os.path.join(
                    self.config['training'].output_path,
                    f"{model_config.name}_final.pth"
                )
                
                torch.save({
                    'model_state_dict': model.state_dict(),
                    'config': asdict(model_config),
                    'metrics': asdict(metrics),
                    'training_result': training_result
                }, model_path)
                
                # ลงทะเบียนโมเดล
                model_id = self.register_model(model, model_config, metrics, model_path)
                
                results[model_config.name] = {
                    'model_id': model_id,
                    'training_result': training_result,
                    'metrics': metrics,
                    'model_path': model_path
                }
                
            except Exception as e:
                logger.error(f"Error training model {model_config.name}: {e}")
                results[model_config.name] = {'error': str(e)}
        
        return results
    
    def _evaluate_model(self, model: nn.Module, test_loader: DataLoader,
                       model_config: ModelConfig) -> ModelMetrics:
        """ประเมินโมเดล"""
        model.eval()
        
        correct = 0
        total = 0
        all_predictions = []
        all_targets = []
        inference_times = []
        
        with torch.no_grad():
            for images, targets in test_loader:
                images = images.to(self.trainer.device)
                
                # Measure inference time
                start_time = time.time()
                outputs = model(images)
                inference_time = (time.time() - start_time) * 1000  # ms
                inference_times.append(inference_time)
                
                # Calculate accuracy (simplified)
                _, predicted = torch.max(outputs.data, 1)
                total += images.size(0)
                correct += predicted.eq(torch.randint(0, model_config.num_classes, (images.size(0),)).to(self.trainer.device)).sum().item()
                
                all_predictions.extend(predicted.cpu().numpy())
                all_targets.extend([0] * len(images))  # Placeholder
        
        accuracy = 100. * correct / total
        avg_inference_time = np.mean(inference_times)
        
        # Calculate model size
        model_size = sum(p.numel() * p.element_size() for p in model.parameters()) / (1024 * 1024)  # MB
        
        # Count parameters
        total_params = sum(p.numel() for p in model.parameters())
        
        return ModelMetrics(
            accuracy=accuracy / 100,
            precision=0.85,  # Placeholder
            recall=0.83,     # Placeholder
            f1_score=0.84,   # Placeholder
            map_50=0.75,     # Placeholder
            map_95=0.65,     # Placeholder
            inference_time_ms=avg_inference_time,
            model_size_mb=model_size,
            flops=1000000,   # Placeholder
            params=total_params
        )
    
    def create_ensemble(self, model_ids: List[str], ensemble_config: EnsembleConfig) -> str:
        """สร้าง ensemble"""
        
        # โหลดโมเดลที่เลือก
        model_paths = {}
        for model_id in model_ids:
            if model_id in self.model_registry:
                model_paths[model_id] = self.model_registry[model_id]['file_path']
        
        # สร้าง ensemble manager
        ensemble_manager = EnsembleManager(ensemble_config)
        ensemble_manager.load_models(model_paths)
        
        # บันทึก ensemble
        ensemble_id = str(uuid.uuid4())
        ensemble_path = os.path.join(
            self.config['training'].output_path,
            f"ensemble_{ensemble_id}.pkl"
        )
        
        with open(ensemble_path, 'wb') as f:
            pickle.dump(ensemble_manager, f)
        
        logger.info(f"Ensemble created: {ensemble_id}")
        return ensemble_id
    
    def run_active_learning(self, model_config: ModelConfig, dataset_path: str,
                           annotations_file: str) -> Dict[str, Any]:
        """รัน Active Learning"""
        
        # สร้าง dataset
        full_dataset = CustomDataset(dataset_path, annotations_file)
        
        # เริ่มต้น active learning
        self.active_learning_manager.initialize_pools(full_dataset)
        
        # สร้างโมเดลเริ่มต้น
        model = self.trainer.create_model(model_config)
        
        # รัน active learning loop
        results = self.active_learning_manager.active_learning_loop(
            model, full_dataset, self.trainer, model_config
        )
        
        # บันทึกผลลัพธ์
        session_id = str(uuid.uuid4())
        
        try:
            conn = sqlite3.connect("advanced_ai.db")
            cursor = conn.cursor()
            
            for i, iteration_result in enumerate(results['iterations']):
                cursor.execute('''
                    INSERT INTO active_learning_sessions 
                    (id, model_id, strategy, iteration, labeled_size, accuracy, queried_samples)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    f"{session_id}_{i}",
                    session_id,
                    self.config['active_learning'].strategy.value,
                    i,
                    results['labeled_sizes'][i],
                    results['accuracies'][i],
                    json.dumps(results['query_history'][i] if i < len(results['query_history']) else {})
                ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Active learning results storage error: {e}")
        
        return results
    
    def get_model_comparison(self, model_ids: List[str]) -> Dict[str, Any]:
        """เปรียบเทียบโมเดล"""
        
        comparison = {
            'models': {},
            'summary': {},
            'recommendations': []
        }
        
        for model_id in model_ids:
            if model_id in self.model_registry:
                model_info = self.model_registry[model_id]
                metrics = model_info['metrics']
                
                comparison['models'][model_id] = {
                    'name': model_info['config'].name,
                    'type': model_info['config'].model_type.value,
                    'accuracy': metrics.accuracy,
                    'f1_score': metrics.f1_score,
                    'inference_time': metrics.inference_time_ms,
                    'model_size': metrics.model_size_mb,
                    'parameters': metrics.params
                }
        
        if comparison['models']:
            # Calculate summary statistics
            accuracies = [m['accuracy'] for m in comparison['models'].values()]
            inference_times = [m['inference_time'] for m in comparison['models'].values()]
            model_sizes = [m['model_size'] for m in comparison['models'].values()]
            
            comparison['summary'] = {
                'best_accuracy': max(accuracies),
                'fastest_inference': min(inference_times),
                'smallest_model': min(model_sizes),
                'avg_accuracy': np.mean(accuracies),
                'avg_inference_time': np.mean(inference_times)
            }
            
            # Generate recommendations
            best_accuracy_model = max(comparison['models'].items(), 
                                    key=lambda x: x[1]['accuracy'])
            fastest_model = min(comparison['models'].items(), 
                              key=lambda x: x[1]['inference_time'])
            
            comparison['recommendations'] = [
                f"Best accuracy: {best_accuracy_model[1]['name']} ({best_accuracy_model[1]['accuracy']:.3f})",
                f"Fastest inference: {fastest_model[1]['name']} ({fastest_model[1]['inference_time']:.1f}ms)",
                f"Consider ensemble for best performance"
            ]
        
        return comparison
    
    def export_model(self, model_id: str, export_format: str = "onnx") -> str:
        """Export โมเดลเป็นรูปแบบต่างๆ"""
        
        if model_id not in self.model_registry:
            raise ValueError(f"Model {model_id} not found")
        
        model_info = self.model_registry[model_id]
        model = model_info['model']
        config = model_info['config']
        
        export_path = os.path.join(
            self.config['training'].output_path,
            f"{config.name}_exported.{export_format}"
        )
        
        if export_format.lower() == "onnx":
            # Export to ONNX
            dummy_input = torch.randn(1, 3, *config.input_size)
            torch.onnx.export(
                model, dummy_input, export_path,
                export_params=True,
                opset_version=11,
                do_constant