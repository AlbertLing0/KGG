"""
PDF处理模块
支持普通PDF文本提取和扫描件OCR识别
"""
import streamlit as st
import pdfplumber
from pdf2image import convert_from_path
import pytesseract
from PIL import Image
import io
import os
import tempfile
import time

# 配置Tesseract路径（Windows系统需要）
# 如果Tesseract已添加到系统PATH，可以注释掉下面这行
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'


def extract_text_from_pdf(pdf_file, use_ocr_only=False):
    """
    从PDF文件中提取文本（文本层 + OCR）
    
    参数:
        pdf_file: Streamlit上传的文件对象或文件路径
        use_ocr_only: 是否仅使用OCR（默认False，会同时提取文本层和OCR）
    
    返回:
        str: 提取的文本内容
    """
    text_layer_content = []  # 文本层内容（按页存储）
    ocr_content = []  # OCR内容（按页存储）
    pdf_path = None
    temp_file_created = False
    
    try:
        # 如果是Streamlit文件对象，需要先保存到临时文件
        if hasattr(pdf_file, 'read'):
            # Streamlit文件对象
            pdf_file.seek(0)  # 确保从文件开头读取
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                tmp_file.write(pdf_file.read())
                pdf_path = tmp_file.name
                temp_file_created = True
                pdf_file.seek(0)  # 重置文件指针
        else:
            # 文件路径
            pdf_path = pdf_file
            temp_file_created = False
        
        page_count = 0
        
        # 第一步：提取文本层（如果有）
        if not use_ocr_only:
            try:
                with pdfplumber.open(pdf_path) as pdf:
                    page_count = len(pdf.pages)
                    for page in pdf.pages:
                        page_text = page.extract_text()
                        text_layer_content.append(page_text if page_text else "")
                
                # 统计文本层提取情况
                text_layer_pages = sum(1 for text in text_layer_content if text.strip())
                if text_layer_pages > 0:
                    st.info(f"📄 从文本层提取了 {text_layer_pages}/{page_count} 页的文本")
            except Exception as e:
                st.warning(f"⚠️ 提取文本层时出错: {str(e)}，将仅使用OCR")
                text_layer_content = [""] * page_count if page_count > 0 else []
        
        # 第二步：OCR识别所有页面（提取图片中的文本）
        st.info("🔄 正在使用OCR识别PDF所有页面（包括图片中的文本），这可能需要一些时间...")
        
        # 将PDF转换为图片
        images = convert_from_path(pdf_path, dpi=300)
        total_pages = len(images)
        
        # 如果之前没有获取页数，使用OCR的页数
        if page_count == 0:
            page_count = total_pages
            if not text_layer_content:
                text_layer_content = [""] * total_pages
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # 对每一页进行OCR识别
        for i, image in enumerate(images):
            status_text.text(f"正在OCR识别第 {i+1}/{total_pages} 页...")
            
            # 使用pytesseract进行OCR（支持中文）
            page_ocr_text = pytesseract.image_to_string(
                image, 
                lang='chi_sim+eng',  # 简体中文+英文
                config='--psm 6'  # 假设是统一的文本块
            )
            
            ocr_content.append(page_ocr_text if page_ocr_text else "")
            
            # 更新进度条
            progress_bar.progress((i + 1) / total_pages)
        
        # 第三步：智能合并文本层和OCR结果
        def simple_similarity(text1, text2):
            """简单的文本相似度检查（检查是否有大量重复）"""
            if not text1 or not text2:
                return False
            # 提取前100个字符进行比较
            t1_short = text1[:100].replace(" ", "").replace("\n", "")
            t2_short = text2[:100].replace(" ", "").replace("\n", "")
            if len(t1_short) < 10 or len(t2_short) < 10:
                return False
            # 简单检查：如果短文本有80%以上相同，认为相似
            common_chars = sum(1 for c in t1_short if c in t2_short)
            similarity = common_chars / max(len(t1_short), len(t2_short))
            return similarity > 0.8
        
        merged_texts = []
        for i in range(page_count):
            text_layer = text_layer_content[i].strip() if i < len(text_layer_content) else ""
            ocr_text = ocr_content[i].strip() if i < len(ocr_content) else ""
            
            # 智能合并策略
            if text_layer and ocr_text:
                # 检查是否高度相似（可能是重复内容）
                if simple_similarity(text_layer, ocr_text):
                    # 如果相似，优先使用文本层（通常更准确），但保留OCR中可能不同的部分
                    merged = text_layer
                    # 如果OCR文本明显更长，可能包含额外信息，追加差异部分
                    if len(ocr_text) > len(text_layer) * 1.5:
                        merged += f"\n\n[OCR补充内容]\n{ocr_text}"
                else:
                    # 不相似，说明OCR提取了图片中的额外文本，合并两者
                    merged = f"{text_layer}\n\n[图片OCR内容]\n{ocr_text}"
            elif text_layer:
                merged = text_layer
            elif ocr_text:
                merged = ocr_text
            else:
                merged = ""
            
            if merged:
                merged_texts.append(merged)
        
        # 合并所有页面的文本
        if len(merged_texts) > 1:
            # 多页时，添加页面分隔符
            final_text = "\n\n".join(
                [f"--- 第 {i+1} 页 ---\n\n{text}" for i, text in enumerate(merged_texts)]
            )
        else:
            # 单页时，直接合并
            final_text = "\n\n".join(merged_texts)
        
        # 统计信息
        text_layer_pages = sum(1 for text in text_layer_content if text.strip())
        ocr_pages = sum(1 for text in ocr_content if text.strip())
        
        if final_text.strip():
            st.success(
                f"✅ 文本提取完成！\n"
                f"   - 文本层: {text_layer_pages}/{page_count} 页\n"
                f"   - OCR识别: {ocr_pages}/{page_count} 页\n"
                f"   - 总页数: {page_count} 页"
            )
            return final_text.strip()
        else:
            st.error("❌ 未能提取到任何文本内容")
            return ""
            
    except Exception as e:
        st.error(f"❌ PDF处理出错: {str(e)}")
        import traceback
        st.error(f"详细错误: {traceback.format_exc()}")
        return ""
    finally:
        # 确保在with块完全结束后再删除临时文件
        if temp_file_created and pdf_path and os.path.exists(pdf_path):
            try:
                # 等待一小段时间，确保文件句柄完全释放
                time.sleep(0.1)
                os.unlink(pdf_path)
            except Exception as e:
                # 如果删除失败，记录警告但不影响程序运行
                # 临时文件会在系统清理时自动删除
                pass


def check_pdf_has_text(pdf_file):
    """
    检查PDF是否包含可提取的文本层
    
    参数:
        pdf_file: Streamlit上传的文件对象或文件路径
    
    返回:
        bool: True表示有文本层，False表示可能是扫描件
    """
    pdf_path = None
    temp_file_created = False
    
    try:
        if hasattr(pdf_file, 'read'):
            # Streamlit文件对象，创建临时文件
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                pdf_file.seek(0)  # 确保从文件开头读取
                tmp_file.write(pdf_file.read())
                pdf_path = tmp_file.name
                temp_file_created = True
                pdf_file.seek(0)  # 重置文件指针，供后续使用
        else:
            # 文件路径
            pdf_path = pdf_file
            temp_file_created = False
        
        # 使用pdfplumber打开文件并检查
        has_text = False
        with pdfplumber.open(pdf_path) as pdf:
            # 检查前几页是否有文本
            sample_pages = min(3, len(pdf.pages))
            for i in range(sample_pages):
                text = pdf.pages[i].extract_text()
                if text and text.strip():
                    has_text = True
                    break
        
        return has_text
        
    except Exception as e:
        st.warning(f"检查PDF文本层时出错: {str(e)}")
        return False
    finally:
        # 确保在with块完全结束后再删除临时文件
        if temp_file_created and pdf_path and os.path.exists(pdf_path):
            try:
                # 等待一小段时间，确保文件句柄完全释放
                time.sleep(0.1)
                os.unlink(pdf_path)
            except Exception as e:
                # 如果删除失败，记录警告但不影响程序运行
                # 临时文件会在系统清理时自动删除
                pass


