import streamlit as st
import json
import os
from datetime import datetime
from utils import generate_graph_data
from streamlit_agraph import agraph, Node, Edge, Config
import re

subgraphs_path = "json_data"

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


def generate_graph_for_each_chapter(chapters):
    """为每一章生成图谱"""
    for idx, chapter in enumerate(chapters):
        chapter_title = chapter['title']
        chapter_content = chapter['content']

        # 调用你的图谱生成函数，假设它返回四个值：nodes_data, edges_data, system_msg, model_name
        nodes_data, edges_data = generate_graph_data(chapter_content, type="subgraph")

        if nodes_data and edges_data:
            # 保存图谱文件
            file_name = save_graph_to_file(nodes_data, edges_data)
            st.write(f"Download the graph for {chapter_title}:")

            # 可视化图谱
            nodes = [Node(id=str(node['id']), label=str(node['label']), size=25) for node in nodes_data]
            edges = [Edge(source=str(edge['from']), target=str(edge['to']), label=str(edge['label'])) for edge in edges_data]
            config = Config(width=1000, height=500, directed=True, physics=True)

            agraph(nodes=nodes, edges=edges, config=config)

def parse_and_merge_json_input(full_graph_json:str =None):
    try:
        graph_data = json.loads(full_graph_json)
        nodes_data = graph_data.get("nodes", [])
        edges_data = graph_data.get("edges", [])
        
        # Correct unpacking here based on the assumption that generate_graph_data returns 4 values
        new_nodes_data, new_edges_data = generate_graph_data(full_graph_json, type="fullgraph")

        # nodes_data.extend(new_nodes_data)
        # edges_data.extend(new_edges_data)

        # FIXME list merge not working here
        merged_nodes_data = list(nodes_data) + list(new_nodes_data)
        merged_edges_data = list(edges_data) + list(new_edges_data)
        
        return merged_nodes_data, merged_edges_data
    except Exception as e:
        st.error(f"Unexpected error during JSON parsing or merging: {e}")
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
        nodes_data, edges_data = generate_graph_data(chapter_content, "subgraph")

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