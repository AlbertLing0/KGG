# PDF上传和OCR功能使用说明

## 功能概述

本项目现已支持PDF文档上传和OCR文本识别功能，可以处理以下两种类型的PDF：

1. **普通PDF**（包含文本层）：直接提取文本，速度快
2. **扫描件PDF**（图片格式）：使用OCR技术识别文本，支持中英文

## 安装依赖

### 1. Python依赖包

```bash
pip install -r requirements.txt
```

新增的依赖包包括：
- `pdfplumber==0.11.0` - PDF文本提取
- `pdf2image==1.17.0` - PDF转图片
- `pytesseract==0.3.13` - OCR识别
- `Pillow==10.4.0` - 图像处理

### 2. Tesseract OCR引擎（必需）

#### Windows系统：
1. 下载安装Tesseract OCR：
   - 下载地址：https://github.com/UB-Mannheim/tesseract/wiki
   - 推荐版本：tesseract-ocr-w64-setup-5.x.x.exe
   
2. 安装时选择中文语言包（chi_sim）

3. 配置环境变量（可选）：
   - 将Tesseract安装路径添加到系统PATH
   - 或修改 `pdf_processor.py` 中的路径配置：
     ```python
     pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
     ```

#### Linux系统：
```bash
sudo apt-get update
sudo apt-get install tesseract-ocr
sudo apt-get install tesseract-ocr-chi-sim  # 中文语言包
```

#### macOS系统：
```bash
brew install tesseract
brew install tesseract-lang  # 包含中文语言包
```

### 3. Poppler工具（PDF转图片需要）

#### Windows系统：
1. 下载Popper：
   - 下载地址：https://github.com/oschwartz10612/poppler-windows/releases/
   - 解压到某个目录（如 `C:\poppler`）

2. 将bin目录添加到系统PATH，或设置环境变量：
   ```python
   # 在pdf_processor.py中，如果需要可以设置：
   # os.environ['PATH'] += os.pathsep + r'C:\poppler\Library\bin'
   ```

#### Linux系统：
```bash
sudo apt-get install poppler-utils
```

#### macOS系统：
```bash
brew install poppler
```

## 使用方法

### 1. 启动应用

```bash
streamlit run app.py
```

### 2. 上传PDF文件

1. 在Web界面中选择 **"PDF文档 (.pdf)"** 选项
2. 点击上传按钮，选择PDF文件
3. 系统会自动检测PDF类型：
   - 如果PDF包含文本层，会提示"检测到PDF包含文本层，将直接提取文本"
   - 如果是扫描件，会提示"检测到PDF可能是扫描件，将使用OCR识别"

### 3. OCR选项

- **自动模式**：系统根据PDF类型自动选择提取方式
- **强制OCR**：勾选"强制使用OCR识别"选项，即使PDF有文本层也会使用OCR（可能获得更好的格式）

### 4. 处理流程

1. **文本提取**：
   - 普通PDF：直接提取，几秒内完成
   - 扫描件PDF：OCR识别，每页需要几秒到十几秒

2. **章节识别**：
   - 自动识别章节标题（格式：第X章）
   - 显示章节预览

3. **知识图谱生成**：
   - 点击"生成子图-合成完整图谱自动化"按钮
   - 系统会为每个章节生成子图，然后合并为完整图谱

## 技术实现

### 文件结构

```
KGG/
├── app.py                 # 主应用（已更新，支持PDF上传）
├── pdf_processor.py       # PDF处理模块（新增）
├── utils.py               # 工具函数
├── llm_utils.py          # LLM调用
└── requirements.txt       # 依赖列表（已更新）
```

### 核心功能

1. **`pdf_processor.py`**：
   - `extract_text_from_pdf()`: 提取PDF文本（支持OCR）
   - `check_pdf_has_text()`: 检查PDF是否包含文本层

2. **处理流程**：
   ```
   PDF上传 → 检测类型 → 提取文本 → 章节分割 → 知识图谱生成
   ```

## 注意事项

1. **OCR处理时间**：
   - OCR识别速度取决于PDF页数和图片质量
   - 建议扫描件PDF页数不超过50页
   - 处理大文件时请耐心等待

2. **识别准确度**：
   - OCR准确度受图片质量影响
   - 建议使用清晰、高分辨率的扫描件
   - 如果识别结果不理想，可以尝试调整扫描参数

3. **系统要求**：
   - 确保已安装Tesseract OCR和Poppler
   - Windows系统需要配置正确的路径
   - 内存建议至少4GB（处理大PDF时）

4. **文件大小限制**：
   - Streamlit默认文件上传限制为200MB
   - 如需上传更大文件，可在启动时设置：
     ```bash
     streamlit run app.py --server.maxUploadSize=500
     ```

## 故障排除

### 问题1：OCR识别失败
- **原因**：Tesseract未安装或路径配置错误
- **解决**：检查Tesseract安装和路径配置

### 问题2：PDF转图片失败
- **原因**：Poppler未安装或路径配置错误
- **解决**：安装Poppler并配置PATH

### 问题3：识别结果乱码
- **原因**：未安装中文语言包
- **解决**：安装 `chi_sim` 语言包

### 问题4：处理速度慢
- **原因**：PDF页数多或图片分辨率高
- **解决**：减少PDF页数或降低图片分辨率

## 后续优化建议

1. **OCR引擎选择**：
   - 可考虑集成PaddleOCR（中文识别效果更好）
   - 或使用云端OCR API（如百度OCR、腾讯OCR）

2. **性能优化**：
   - 多线程处理多页PDF
   - 缓存OCR结果
   - 支持断点续传

3. **用户体验**：
   - 添加处理进度条
   - 支持批量上传
   - 提供OCR结果预览和编辑功能

## 更新日志

- **2024-XX-XX**: 初始版本，支持PDF上传和OCR识别





