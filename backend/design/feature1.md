# 特征1：视觉目的地验证系统设计文档

## 概述

### 目标
实现一个两阶段视觉验证系统，用于确认导航小车是否准确到达目标位置（如 `toilet`, `emergency_clinic` 等）。系统通过车载摄像头捕获图像，使用自训练的黑色粗框分割模型提取文本标签区域（文本标签周围有黑色粗框包围），然后通过OCR模型识别文本内容，最后与预期的 `destination_clinic_id` 进行匹配验证。

### 核心需求
1. **自训练模型需求**：训练一个黑色粗框分割模型（DeepLabV3 MobileNetV2）
2. **识别需求**：使用现成OCR模型进行文本识别
3. **集成需求**：与现有导航系统无缝对接
4. **实时性需求**：验证过程需在合理时间内完成（<200ms）
5. **Coral TPU兼容性**：模型应兼容Coral TPU硬件加速

## 系统架构

### 整体流程图
```
[车载摄像头] → [cv2图像捕获] → [图像预处理]
        ↓
[自训练黑色粗框分割模型] → [黑色粗框掩码/轮廓]
        ↓
[区域裁剪] → [OCR模型] → [识别文本]
        ↓
[文本清洗] → [与destination_clinic_id匹配] → [验证结果]
```

### 模块划分

#### 1. 图像捕获模块 (`src/vision/camera_capture.py`)
- 使用 `cv2.VideoCapture` 捕获车载摄像头图像
- 图像预处理：去畸变、白平衡、对比度调整
- 专为验证优化的捕获模式

#### 2. 黑色粗框分割模型（自训练） (`src/vision/black_box_segmenter.py`)
- 负责分割图像中的黑色粗框区域
- 输出分割掩码或轮廓点
- 模型类型：DeepLabV3 MobileNetV2（推荐）、U-Net（备选）

#### 3. OCR识别模块 (`src/vision/ocr_recognizer.py`)
- 使用现成OCR库（EasyOCR/Tesseract/PaddleOCR）
- 识别文本区域中的文字内容
- 返回识别文本及置信度

#### 4. 验证逻辑模块 (`src/vision/destination_verifier.py`)
- 整合检测和识别流程
- 文本清洗和标准化
- 与 `destination_clinic_id` 进行匹配验证
- 返回验证结果及置信度

#### 5. API路由模块 (`src/router/vision_navigation.py`)
- 提供验证API端点
- 处理图像上传和参数传递
- 返回结构化验证结果

## 技术栈选择

### 推荐方案：DeepLabV3 MobileNetV2 + EasyOCR

#### 文本区域分割模型：DeepLabV3 with MobileNetV2 Backbone
**选择理由：**
- ✅ **专门用于分割**：像素级分割能力，能精确分割黑色粗框区域
- ✅ **轻量级架构**：MobileNetV2 backbone参数量小，适合边缘部署
- ✅ **Coral TPU兼容**：MobileNetV2架构与Coral TPU兼容，可硬件加速
- ✅ **训练数据需求低**：黑色粗框特征明确，所需训练数据量少（可能仅需几十张图像）
- ✅ **鲁棒性强**：对视角变化、光照变化具有一定鲁棒性

**训练配置：**
```bash
# 使用PyTorch和segmentation models库
python train_segmentation.py --model deeplabv3_mobilenetv2 --epochs 30 --batch-size 8
```

#### OCR模型：EasyOCR
**选择理由：**
- ✅ **开箱即用**：`pip install easyocr` 即可使用
- ✅ **多语言支持**：支持中文/英文混合识别
- ✅ **准确率高**：基于深度学习的OCR引擎
- ✅ **无需训练**：使用预训练模型

**使用方式：**
```python
import easyocr
reader = easyocr.Reader(['en'])
results = reader.readtext(image, detail=0)
```

### 备选方案
1. **分割模型备选**：
   - U-Net：轻量级分割架构，训练简单但可能精度略低
   - DeepLabV3+：更先进的空洞卷积，精度更高但计算量更大

2. **OCR备选**：
   - Tesseract：成熟稳定，但场景文本识别有限
   - PaddleOCR：中文识别优秀，但依赖较多

## 数据集与训练

### 数据收集策略
1. **标注内容**：在纸质地图的每个 `main` 节点位置放置带黑色粗框的文本标签
2. **数据量目标**：200-300张图像（每个位置15-25张） - 黑色粗框特征明确，所需数据量减少
3. **多样性要求**：
   - 不同角度（俯视、斜视、平视，特别是文本标签垂直放置的情况）
   - 不同光照条件（正常光、弱光、强光）
   - 不同距离（近、中、远）
   - 部分遮挡情况（模拟实际环境）

### 标注格式
```
分割掩码格式（PASCAL VOC样式）：
- 每个图像对应一个XML标注文件
- 包含黑色粗框区域的多边形坐标点
- 类别：black_bold_box

或使用COCO格式的JSON标注文件
```

### 数据集结构
```
datasets/black_box_labels/
├── images/
│   ├── toilet_001.jpg
│   ├── toilet_002.jpg
│   └── emergency_clinic_001.jpg
├── annotations/
│   ├── toilet_001.xml  # 或 toilet_001.json
│   ├── toilet_002.xml
│   └── emergency_clinic_001.xml
├── train.txt      # 训练集图像路径列表
├── val.txt        # 验证集图像路径列表
└── classes.txt    # 类别定义文件
```

### 类别定义示例
```
# classes.txt
black_bold_box
```

## 实施路线图

### Phase 1：数据收集与标注（1-2天）
**目标**：收集和标注训练数据集
1. 在12个 `main` 节点位置放置带黑色粗框的文本标签
2. 多角度、多光照条件拍摄图像（特别关注文本标签垂直放置的情况）
3. 使用labelme工具进行像素级标注（标注黑色粗框区域）
4. 划分训练集/验证集（80/20比例）

**交付物**：
- 标注完成的图像数据集
- 分割掩码标注文件（XML或JSON格式）
- 类别定义文件

### Phase 2：模型训练（2-4天）
**目标**：训练黑色粗框分割模型
1. 搭建PyTorch和segmentation models库环境
2. 准备分割数据集加载和预处理
3. 训练DeepLabV3 MobileNetV2模型（30-50 epochs）
4. 模型评估和优化（IoU, Precision, Recall指标）
5. 导出为部署格式（ONNX/TFLite，考虑Coral TPU兼容性）

**交付物**：
- 训练好的分割模型文件（.pth或.onnx）
- 训练日志和性能报告
- 模型评估指标（IoU, Precision, Recall）

### Phase 3：系统集成（2-3天）
**目标**：实现完整的验证系统
1. 实现图像捕获模块
2. 集成EasyOCR识别器
3. 开发验证逻辑模块
4. 创建API路由和端点
5. 编写单元测试和集成测试

**交付物**：
- 完整的视觉验证代码模块
- API端点 `/api/vision/verify_destination`
- 测试脚本和示例

### Phase 4：测试与优化（2-3天）
**目标**：系统测试和性能优化
1. 端到端功能测试
2. 性能测试和瓶颈分析
3. 模型优化（量化、剪枝）
4. 错误处理完善
5. 文档编写

**交付物**：
- 测试报告和性能数据
- 优化后的部署模型
- 用户文档和API文档

## 与现有系统集成

### 数据流集成
```
现有导航流程：
用户输入 → 智能分诊 → 路径规划 → parse_commands → 小车执行指令

新增验证流程：
小车执行完成 → 摄像头捕获图像 → 视觉验证API → 匹配验证 → 结束导航/重试
```

### API设计

#### 验证端点
```python
POST /api/vision/verify_destination
请求体：
{
    "image": "base64编码的图像数据",
    "expected_id": "toilet"  # destination_clinic_id
}

响应体：
{
    "success": true,
    "verified": true,
    "data": {
        "matched_text": "toilet",
        "confidence": 0.95,
        "bbox": [x1, y1, x2, y2],
        "processing_time_ms": 75
    }
}
```

#### 前端调用示例
```javascript
async function verifyArrival(expectedClinicId) {
    // 1. 后端摄像头捕获图像
    const imageBlob = await captureCarCameraImage();

    // 2. 调用验证API
    const formData = new FormData();
    formData.append('image', imageBlob, 'capture.jpg');
    formData.append('expected_id', expectedClinicId);

    const response = await fetch('/api/vision/verify_destination', {
        method: 'POST',
        body: formData
    });

    return await response.json();
}
```

### 代码结构扩展
```
backend/src/
├── vision/                    # 新增视觉模块
│   ├── __init__.py
│   ├── camera_capture.py     # 图像捕获
│   ├── black_box_segmenter.py # 黑色粗框分割模型
│   ├── ocr_recognizer.py     # OCR识别
│   └── destination_verifier.py # 验证逻辑
├── router/
│   ├── __init__.py
│   └── vision_navigation.py  # 新增视觉导航路由
└── models/                   # 模型文件目录
    └── black_box_segmenter.pth # 训练好的分割模型
```

## 性能预期

### 处理时间预估
| 组件 | 处理时间 | 硬件要求 |
|------|----------|----------|
| 图像捕获 | ~10ms | USB摄像头 |
| 图像预处理 | ~5ms | CPU |
| DeepLabV3 MobileNetV2推理 | ~30-50ms (CPU) / ~10-15ms (Coral TPU) | CPU或Coral TPU加速 |
| 掩码后处理 | ~5ms | CPU |
| EasyOCR识别 | ~50ms | CPU |
| 文本匹配 | ~1ms | CPU |
| **总计** | **~101-121ms (CPU) / ~81-91ms (Coral TPU)** | **满足实时性要求** |

### 资源需求
- **训练阶段**：需要GPU（推荐4GB+显存）
- **部署阶段**：CPU可运行，Coral TPU可大幅加速
- **内存占用**：~400MB（模型+运行时）
- **存储空间**：~150MB（模型文件+依赖）
- **Coral TPU兼容性**：MobileNetV2 backbone与Coral TPU兼容，可部署为TFLite格式

## 风险评估与缓解

### 风险1：分割模型精度不足
**风险描述**：黑色粗框分割准确率低，影响后续OCR识别
**缓解措施**：
- 收集多样化的训练数据（特别是不同角度和光照）
- 数据增强技术（旋转、缩放、色彩变换、模拟遮挡）
- 使用更先进的分割架构（如DeepLabV3+）
- 设置IoU阈值，低质量分割时触发重试

### 风险2：OCR识别错误
**风险描述**：相似文本识别错误（如"internal" vs "emergency"）
**缓解措施**：
- 文本清洗和标准化
- 模糊匹配算法（Levenshtein距离）
- 多OCR引擎投票机制
- 人工可读的备选建议

### 风险3：环境变化影响
**风险描述**：光照、角度变化导致检测失败
**缓解措施**：
- 训练数据覆盖多种环境条件
- 实时图像预处理（自适应直方图均衡化）
- 多帧验证机制
- 失败时自动调整摄像头角度重试

### 风险4：系统集成复杂度
**风险描述**：与现有导航系统集成困难
**缓解措施**：
- 模块化设计，最小化耦合
- 明确定义的API接口
- 分阶段集成测试
- 详细的日志和错误处理

## 验收标准

### 功能验收
- [ ] 能够正确捕获车载摄像头图像
- [ ] 黑色粗框分割模型IoU >80% （分割质量）
- [ ] OCR识别准确率 >90% （清洁图像条件下）
- [ ] 端到端验证成功率 >80%
- [ ] 平均处理时间 <200ms （CPU）/ <100ms （Coral TPU）
- [ ] API接口稳定，错误处理完善

### 集成验收
- [ ] 与现有导航系统无缝集成
- [ ] 前端能够正确调用验证API
- [ ] 验证结果能够正确影响导航流程
- [ ] 系统日志完整，便于调试

### 文档验收
- [ ] 完整的API文档
- [ ] 模型训练和部署指南
- [ ] 故障排除手册
- [ ] 性能测试报告

## 后续扩展方向

### 短期扩展（1-2个月）
1. **多模态验证**：结合颜色标记、形状识别等其他视觉特征
2. **动态重试机制**：验证失败时自动调整位置重试
3. **模型持续学习**：根据实际使用数据优化模型

### 中期扩展（3-6个月）
1. **语义理解**：不依赖预设标签，理解环境语义
2. **多摄像头融合**：结合不同角度的摄像头信息
3. **3D定位**：结合深度信息进行精确位置验证

### 长期扩展（6-12个月）
1. **端到端学习**：直接从图像到导航决策的端到端模型
2. **跨环境泛化**：适应不同医院环境，无需重新训练
3. **主动感知**：主动探索环境，构建认知地图

## 附录

### A. 依赖安装清单
```bash
# 核心依赖
pip install opencv-python numpy

# 分割模型训练和推理
pip install torch torchvision
pip install segmentation-models-pytorch  # 或使用timm库

# OCR识别
pip install easyocr

# 图像处理
pip install pillow imutils

# 标注工具（可选）
pip install labelme  # 用于创建分割标注

# Coral TPU支持（可选）
# 如需部署到Coral TPU，需要安装TensorFlow Lite和Edge TPU运行时

# API开发
# 已包含在现有FastAPI环境中
```

### B. 硬件配置建议
- **摄像头**：1080p USB摄像头，60FPS以上
- **处理器**：Intel i5 8代以上或同等性能
- **内存**：8GB RAM（推荐16GB）
- **存储**：256GB SSD（用于模型存储）
- **可选GPU**：NVIDIA GTX 1060 4GB以上（用于训练）

### C. 参考资料
1. DeepLabV3论文和实现：https://arxiv.org/abs/1706.05587
2. Segmentation Models PyTorch库：https://github.com/qubvel/segmentation_models.pytorch
3. EasyOCR文档：https://github.com/JaidedAI/EasyOCR
4. OpenCV摄像头操作：https://docs.opencv.org/
5. FastAPI文件上传：https://fastapi.tiangolo.com/tutorial/request-files/
6. Coral TPU文档：https://coral.ai/docs/

---
**文档版本**：v1.1
**创建日期**：2026-03-05
**最后更新**：2026-03-05
**负责人**：视觉验证系统设计团队
**更新摘要**：根据最新讨论更新技术方案，采用DeepLabV3 MobileNetV2分割黑色粗框，集成Coral TPU加速支持