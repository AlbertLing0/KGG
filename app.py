import streamlit as st
import json
import time
import os
from datetime import datetime
from utils import generate_graph_data  # Ensure this returns 4 values (nodes, edges, system_msg, model_name)
from streamlit_agraph import agraph, Node, Edge, Config
from docx import Document
import re
from pdf_processor import extract_text_from_pdf, check_pdf_has_text

st.set_page_config(page_title="Knowledge Graph Generator", layout="wide")
st.title("知识图谱生成测试专用页面")
# text_input = st.text_area("Input Text", height=200)
# json_input = st.text_area("Input Previous Knowledge Graph (JSON)", height=200, help="Paste the previous knowledge graph JSON here.")


if 'graph_data' not in st.session_state:
    st.session_state.graph_data = None
if 'agraph_config' not in st.session_state:
    st.session_state.agraph_config = None
if 'graph_ready' not in st.session_state:
    st.session_state.graph_ready = False

nodes_data = []
edges_data = []
# 用于保存子图的路径
subgraphs_path = "json_data"

if not os.path.exists(subgraphs_path):
    os.makedirs(subgraphs_path)
model_options = [
    "/mnt/chenbaiming/gpt-oss-120b"
]

st.sidebar.header("Model Selection")
selected_model = st.sidebar.selectbox("Choose your model:", model_options, index=model_options.index(
    st.session_state.current_model) if 'current_model' in st.session_state else 0)
st.session_state.current_model = selected_model

def split_into_chapters(text):
    """
    根据章节标题切分文本，假设章节标题格式为 "第1章" 或 "第 1 章"
    """
    # 更新的正则表达式，匹配有空格的章节标题
    # chapter_pattern = re.compile(r'(第\s?[一二三四五六七八九十]?\s?[0-9]+章|第\s?[一二三四五六七八九十]+\s?章)\s*(.*?)\s*(?=\n|$)')
    # chapter_pattern = re.compile(r'(第\s?[一二三四五六七八九十0-9]+\s?章)\s*(.*?)\s*(?=\n|$)')
    chapter_pattern = re.compile(r'(第\s?[一二三四五六七八九十0-9]+[\s]?[章])\s*(.*?)\s*(?=\n|$)')


    chapters = []
    current_chapter = None

    # 分割文本并去除空行
    lines = [line.strip() for line in text.split("\n") if line.strip()]

    for line in lines:
        match = chapter_pattern.match(line)
        if match:
            if current_chapter:
                chapters.append(current_chapter)
            current_chapter = {"title": match.group(1) + " " + match.group(2), "content": ""}
        if current_chapter:
            current_chapter["content"] += line + "\n"

    if current_chapter:
        chapters.append(current_chapter)

    return chapters

def prepare_graph_visualization(nodes_data, edges_data):
    nodes = [
        Node(
            id=str(node['id']),
            label=str(node['label']),
            size=25,
            color=f"#{hash(str(node['group'])) % 0xFFFFFF:06x}"
        ) for node in nodes_data
    ]

    edges = [
        Edge(
            source=str(edge['from']),
            target=str(edge['to']),
            label=str(edge['label'])
        ) for edge in edges_data
    ]

    config = Config(
        width=1000,
        height=500,
        directed=True,
        physics=True,
        hierarchical=True,
        nodeHighlightBehavior=True,
        highlightColor="#F7A7A6",
        collapsible=True,
        node={'labelProperty': 'label'},
        link={'labelProperty': 'label', 'renderLabel': True}
    )

    return nodes, edges, config


def extract_knowledge(type, textbook_type="通用"):
    if not text_input:
        st.warning("Please enter text first.")
        return [], [], '', ''

    try:
        # Assuming generate_graph_data returns 4 values (nodes_data, edges_data, system_msg, model_name)
        nodes_data, edges_data = generate_graph_data(text_input, type=type, textbook_type=textbook_type)
        
        if not nodes_data or not edges_data:
            st.warning("Failed to extract valid knowledge graph. Please modify your input text.")
            st.session_state.graph_ready = False
            return [], [], '', ''

        st.session_state.graph_data = (nodes_data, edges_data)
        nodes, edges, config = prepare_graph_visualization(nodes_data, edges_data)
        st.session_state.agraph_config = {
            'nodes': nodes,
            'edges': edges,
            'config': config
        }
        st.session_state.graph_ready = True
        return nodes_data, edges_data
    except Exception as e:
        st.error(f"Error during knowledge extraction: {str(e)}")
        return [], [], '', ''

def save_graph_to_file(nodes_data, edges_data, chapter_title):
    """保存每章的图谱为文件"""
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    file_name = f"chapter_graph_{chapter_title}_{timestamp}.json"
    file_path = os.path.join("json_data", file_name)

    graph_data = {
        "nodes": nodes_data,
        "edges": edges_data
    }

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(graph_data, f, ensure_ascii=False, indent=4)

    st.success(f"Graph for '{chapter_title}' saved as {file_name}")
    return file_name


def generate_graph_for_each_chapter(chapters, textbook_type="通用"):
    """为每一章生成图谱"""
    for idx, chapter in enumerate(chapters):
        chapter_title = chapter['title']
        chapter_content = chapter['content']

        # 调用你的图谱生成函数，假设它返回四个值：nodes_data, edges_data, system_msg, model_name
        nodes_data, edges_data = generate_graph_data(chapter_content, type="subgraph", textbook_type=textbook_type)

        if nodes_data and edges_data:
            # 保存图谱文件
            file_name = save_graph_to_file(nodes_data, edges_data)
            st.write(f"Download the graph for {chapter_title}:")

            # 可视化图谱
            nodes = [Node(id=str(node['id']), label=str(node['label']), size=25) for node in nodes_data]
            edges = [Edge(source=str(edge['from']), target=str(edge['to']), label=str(edge['label'])) for edge in edges_data]
            config = Config(width=1000, height=500, directed=True, physics=True)

            agraph(nodes=nodes, edges=edges, config=config)

def parse_and_merge_json_input(full_graph_json=None, text_input=None):
    """
    解析并合并JSON图谱
    
    参数:
        full_graph_json: 已有的完整图谱JSON字符串
        text_input: 可选的文本输入（用于扩展图谱）
    
    返回:
        tuple: (nodes_data, edges_data)
    """
    try:
        if not full_graph_json:
            st.error("未提供图谱JSON数据")
            return [], []
        
        # 解析已有的图谱JSON
        graph_data = json.loads(full_graph_json)
        nodes_data = graph_data.get("nodes", [])
        edges_data = graph_data.get("edges", [])
        
        # 获取教材类型，如果没有设置则使用默认值
        textbook_type = st.session_state.get('textbook_type', '通用')
        
        # 如果有新的文本输入，用于扩展图谱
        if text_input and isinstance(text_input, str) and text_input.strip():
            # 将已有图谱作为JSON输入传递给generate_graph_data
            new_nodes_data, new_edges_data = generate_graph_data(
                text_input, 
                json_input=full_graph_json, 
                type="fullgraph",
                textbook_type=textbook_type
            )
            
            # 合并新旧数据
            nodes_data.extend(new_nodes_data)
            edges_data.extend(new_edges_data)
        else:
            # 如果没有新文本，只是标准化已有图谱
            # 传入描述性文本，让LLM标准化图谱结构（添加课程节点等）
            standardize_text = "请标准化这个知识图谱，添加课程节点（ID=0）并连接所有章节节点。"
            new_nodes_data, new_edges_data = generate_graph_data(
                standardize_text, 
                json_input=full_graph_json, 
                type="fullgraph",
                textbook_type=textbook_type
            )
            
            # 如果生成了新数据，使用新数据；否则使用原有数据
            if new_nodes_data and new_edges_data:
                nodes_data = new_nodes_data
                edges_data = new_edges_data

        return nodes_data, edges_data
    except json.JSONDecodeError as e:
        st.error(f"JSON解析错误: {str(e)}")
        return [], []
    except Exception as e:
        st.error(f"合并图谱时出错: {str(e)}")
        import traceback
        st.error(f"详细错误: {traceback.format_exc()}")
        return [], []


def save_graph_to_file(nodes_data, edges_data):
    # 时间戳命名
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    file_name = f"kg_{timestamp}.json"
    file_path = os.path.join("json_data", file_name)

    graph_data = {
        "nodes": nodes_data,
        "edges": edges_data
    }

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(graph_data, f, ensure_ascii=False, indent=4)

    st.success(f"Graph saved as {file_name}")
    return file_name

# 为每一章生成子图
def generate_subgraph_for_chapters(chapters):
    """为每一章生成图谱，并自动合并"""
    subgraph_files = []
    for idx, chapter in enumerate(chapters):
        chapter_title = chapter['title']
        chapter_content = chapter['content']

        # 提取章节编号，比如"第8章"、"第12章"，忽略后面的文字
        match = re.search(r'(第\s*\d+\s*章|第\s*[一二三四五六七八九十]+\s*章)', chapter_title)
        if match:
            chapter_short_title = match.group(1).replace(" ", "")  # 去除多余空格
        else:
            chapter_short_title = f"Chapter{idx+1}"  # 如果没匹配上，兜底用索引命名

        # 生成干净的文件名
        file_name = f"{chapter_short_title}.json"
        file_path = os.path.join(subgraphs_path, file_name)

        # 生成子图数据
        # 获取教材类型，如果没有设置则使用默认值
        textbook_type = st.session_state.get('textbook_type', '通用')
        nodes_data, edges_data = generate_graph_data(chapter_content, type="subgraph", textbook_type=textbook_type)

        if nodes_data and edges_data:
            # 保存子图文件
            graph_data = {"nodes": nodes_data, "edges": edges_data}
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(graph_data, f, ensure_ascii=False, indent=4)
            subgraph_files.append(file_path)

            # 展示子图
            nodes = [Node(id=str(node['id']), label=str(node['label']), size=25) for node in nodes_data]
            edges = [Edge(source=str(edge['from']), target=str(edge['to']), label=str(edge['label'])) for edge in edges_data]
            config = Config(width=1000, height=500, directed=True, physics=True)

            with st.expander(f"Subgraph for {chapter_title}", expanded=False):
                agraph(nodes=nodes, edges=edges, config=config)

    return subgraph_files


# 合并子图为一个完整的图谱
def merge_subgraphs(subgraph_files):
    """合并所有子图文件，生成完整图谱"""
    all_nodes = []
    all_edges = []
    
    for subgraph_file in subgraph_files:
        with open(subgraph_file, "r", encoding="utf-8") as f:
            subgraph_data = json.load(f)
            all_nodes.extend(subgraph_data.get("nodes", []))
            all_edges.extend(subgraph_data.get("edges", []))

    # 创建一个完整图谱
    full_graph = {
        "nodes": all_nodes,
        "edges": all_edges
    }

    full_graph_file_name = f"full_knowledge_graph_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.json"
    full_graph_file_path = os.path.join(subgraphs_path, full_graph_file_name)

    with open(full_graph_file_path, "w", encoding="utf-8") as f:
        json.dump(full_graph, f, ensure_ascii=False, indent=4)

    st.success(f"Full graph saved as {full_graph_file_name}")
    return full_graph_file_path


# 文件上传区域
st.subheader("📄 上传文档")
file_type = st.radio(
    "选择文件类型:",
    ["Word文档 (.docx)", "PDF文档 (.pdf)"],
    horizontal=True
)

uploaded_file = None
text = ""

if file_type == "Word文档 (.docx)":
    uploaded_file = st.file_uploader("上传Word文档", type="docx", help="支持.docx格式的Word文档")
    if uploaded_file:
        try:
            # 读取 Word 文档
            doc = Document(uploaded_file)
            
            # 提取所有段落的文本
            text = "\n".join([para.text for para in doc.paragraphs])

            st.success("✅ Word文档加载成功！")
            
        except Exception as e:
            st.error(f"❌ 读取Word文档失败: {str(e)}")
            text = ""

elif file_type == "PDF文档 (.pdf)":
    uploaded_file = st.file_uploader("上传PDF文档", type="pdf", help="自动提取文本层和OCR识别图片中的文本")
    
    if uploaded_file:
        # 检查PDF类型（仅用于显示信息）
        has_text = check_pdf_has_text(uploaded_file)
        
        if has_text:
            st.info("📄 检测到PDF包含文本层，将同时提取文本层和OCR识别图片中的文本")
        else:
            st.info("🖼️ 检测到PDF可能是扫描件，将使用OCR识别所有页面")
        
        # 提供选项：是否仅使用OCR（跳过文本层提取）
        use_ocr_only = st.checkbox("仅使用OCR识别（跳过文本层提取）", value=False, 
                                   help="勾选后将跳过文本层提取，仅使用OCR识别，适用于纯扫描件PDF")
        
        # 默认行为：同时提取文本层和OCR
        # 如果勾选了仅OCR，则只进行OCR
        text = extract_text_from_pdf(uploaded_file, use_ocr_only=use_ocr_only)

# 处理提取的文本
chapters = []
if text and uploaded_file:
    chapters = split_into_chapters(text)
    
    if chapters:
        st.success(f"✅ 成功提取文本，共识别 {len(chapters)} 个章节")
        
        # 显示章节预览
        with st.expander("📖 章节预览", expanded=False):
            for idx, chapter in enumerate(chapters):
                st.subheader(f"第 {idx + 1} 章: {chapter['title']}")
                st.text_area(
                    f"章节内容: {chapter['title']}", 
                    chapter['content'], 
                    height=200,
                    key=f"chapter_{idx}"
                )
    else:
        st.warning("⚠️ 未能识别到章节，将使用全部文本内容")
        chapters = [{"title": "全文", "content": text}]
    
    # 教材类型选择
    st.subheader("📚 教材类型设置")
    textbook_type = st.selectbox(
        "选择教材类型:",
        ["通用", "理工科", "人文社科", "实际工作手册"],
        index=0,
        help="根据教材类型选择不同的知识图谱生成策略。理工科侧重公式定理和逻辑推导；人文社科侧重理论观点和历史脉络；工作手册侧重流程步骤和实用方法。"
    )
    
    # 显示教材类型说明
    type_descriptions = {
        "通用": "适用于一般性教材，提取章节、小节、知识点和基本关系",
        "理工科": "适用于数学、物理、工程等学科，重点提取公式、定理、算法和逻辑推导关系",
        "人文社科": "适用于历史、文学、哲学等学科，重点提取理论、观点、人物和历史发展脉络",
        "实际工作手册": "适用于操作手册、工作指南等，重点提取流程、步骤、工具和实用方法"
    }
    st.info(f"📌 {type_descriptions[textbook_type]}")
    
    # 保存到session_state，供后续按钮使用
    st.session_state.chapters = chapters
    st.session_state.extracted_text = text
    st.session_state.textbook_type = textbook_type
elif 'chapters' in st.session_state:
    # 如果之前有章节数据，继续使用
    chapters = st.session_state.chapters
    # 如果没有设置教材类型，使用默认值
    if 'textbook_type' not in st.session_state:
        st.session_state.textbook_type = "通用"

# if st.button("Generate Subgraphs for All Chapters"):
#     start_time = time.time()

#     with st.spinner('Generating subgraphs for all chapters...'):
#         subgraph_files = generate_subgraph_for_chapters(chapters)

#         # 合并所有子图
#         full_graph_file = merge_subgraphs(subgraph_files)

#         # 加载合并后的完整图谱
#         with open(full_graph_file, 'r', encoding='utf-8') as f:
#             full_graph_data = json.load(f)
        
#         nodes_data = full_graph_data.get("nodes", [])
#         edges_data = full_graph_data.get("edges", [])

#         # 渲染到页面
#         if nodes_data and edges_data:
#             st.success("✅ Full graph generated successfully! Now rendering...")
#             nodes, edges, config = prepare_graph_visualization(nodes_data, edges_data)
#             agraph(
#                 nodes=nodes,
#                 edges=edges,
#                 config=config
#             )
#         else:
#             st.error("❌ Full graph data is empty.")

#     end_time = time.time()
#     execution_time = end_time - start_time
#     st.write(f"🕒 This operation took {execution_time:.2f} seconds to complete.")

if st.button("生成子图-合成完整图谱自动化"):
    # 检查是否有章节数据
    if 'chapters' not in st.session_state or not st.session_state.chapters:
        st.error("❌ 请先上传文档并提取文本！")
    else:
        chapters = st.session_state.chapters
    start_time = time.time()

    with st.spinner('生成子图...'):
        subgraph_files = generate_subgraph_for_chapters(chapters)

        # 合并所有子图
        full_graph_file = merge_subgraphs(subgraph_files)

        # 读取合并后的JSON内容作为新的input
        with open(full_graph_file, 'r', encoding='utf-8') as f:
            merged_json_text = f.read()
        st.success("✅ 子图生成、合并完毕")
        # 调用 parse_and_merge_json_input 重新解析，走 fullgraph 逻辑
        try:
            # 传入合并后的JSON，用于标准化图谱结构
            nodes_data, edges_data = parse_and_merge_json_input(
                full_graph_json=merged_json_text,
                text_input=None  # 不需要新文本，只是标准化已有图谱
            )

            # 渲染标准化后的完整图谱
            if nodes_data and edges_data:
                st.success("✅ Full graph generated and standardized successfully! Now rendering...")
                nodes, edges, config = prepare_graph_visualization(nodes_data, edges_data)
                agraph(
                    nodes=nodes,
                    edges=edges,
                    config=config
                )
            else:
                st.error("❌ Full graph data after merging is empty.")

        except Exception as e:
            st.error(f"Error during re-parsing full graph: {str(e)}")

    end_time = time.time()
    execution_time = end_time - start_time
    st.write(f"🕒 This operation took {execution_time:.2f} seconds to complete.")
        
# if st.button("Generate Subgraph"):
#     start_time = time.time()  # Record the start time

#     with st.spinner('Generating subgraph...'):
#         if json_input:
#             # Use the first system prompt if json_input exists
#             nodes_data, edges_data = parse_and_merge_json_input()
#         else:
#             # If no json_input, generate graph based only on text_input using the first system prompt
#             nodes_data, edges_data = extract_knowledge("subgraph")

#         if nodes_data and edges_data:
#             # Save the generated subgraph to a file
#             file_name = save_graph_to_file(nodes_data, edges_data)
#             st.write(f"Download the subgraph file: {file_name}")

#             with st.expander("Subgraph", expanded=True):
#                 st.write("Nodes:")
#                 st.write(nodes_data)
#                 st.write("Edges:")
#                 st.write(edges_data)

#             try:
#                 # Display the subgraph using stored configuration
#                 nodes, edges, config = prepare_graph_visualization(nodes_data, edges_data)
#                 return_value = agraph(
#                     nodes=nodes,
#                     edges=edges,
#                     config=config
#                 )
#             except Exception as e:
#                 st.error(f"Error displaying subgraph: {str(e)}")

#     end_time = time.time()  # Record the end time
#     execution_time = end_time - start_time  # Calculate the time taken
#     st.write(f"🕒 This operation took {execution_time:.2f} seconds to complete.")  # Display the time taken

# if st.button("Generate Full Graph"):
#     start_time = time.time()  # Record the start time

#     with st.spinner('Generating full graph...'):
#         # Use second system prompt when json_input exists
#         nodes_data, edges_data, system_msg, model_name = parse_and_merge_json_input()

#         if nodes_data and edges_data:
#             # Save the generated full graph to a file
#             file_name = save_graph_to_file(nodes_data, edges_data)
#             st.write(f"Download the full graph file: {file_name}")

#             with st.expander("Full Graph", expanded=True):
#                 st.write("Nodes:")
#                 st.write(nodes_data)
#                 st.write("Edges:")
#                 st.write(edges_data)

#             try:
#                 # Display the full graph using stored configuration
#                 nodes, edges, config = prepare_graph_visualization(nodes_data, edges_data)
#                 return_value = agraph(
#                     nodes=nodes,
#                     edges=edges,
#                     config=config
#                 )
#             except Exception as e:
#                 st.error(f"Error displaying full graph: {str(e)}")

#     end_time = time.time()  # Record the end time
#     execution_time = end_time - start_time  # Calculate the time taken
#     st.write(f"🕒 This operation took {execution_time:.2f} seconds to complete.")  # Display the time taken


# 渲染 JSON 图谱功能（独立）
st.subheader("Render Graph from JSON Text")
json_input_for_rendering = st.text_area("Enter Graph JSON to Render", height=200, help="Paste the entire graph JSON here.")

if st.button("Render Graph from JSON"):
    if json_input_for_rendering:
        try:
            graph_data = json.loads(json_input_for_rendering)
            nodes_data = graph_data.get("nodes", [])
            edges_data = graph_data.get("edges", [])

            if nodes_data and edges_data:
                st.write("Rendering graph...")
                nodes, edges, config = prepare_graph_visualization(nodes_data, edges_data)
                return_value = agraph(
                    nodes=nodes,
                    edges=edges,
                    config=config
                )
            else:
                st.error("Invalid graph data.")
        except json.JSONDecodeError as e:
            st.error(f"Invalid JSON format: {e}")
    else:
        st.error("Please input a valid JSON graph.")
