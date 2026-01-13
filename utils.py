import json
from llm_utils import call_llm
import streamlit as st

def detect_language(text):
    """Detect the primary language of the input text"""
    # Simple language detection based on character sets
    chinese_chars = len([c for c in text if '\u4e00' <= c <= '\u9fff'])
    english_chars = len([c for c in text if c.isascii() and c.isalpha()])

    return 'chinese' if chinese_chars > english_chars else 'english'


def get_system_prompt(language, is_extension=False, type="subgraph", textbook_type="通用"):
    """Get system prompt based on language, extension flag, and textbook type"""
    
    # 根据教材类型选择不同的提示词
    if type == "subgraph":
        # 理工科教材提示词
        if textbook_type == "理工科":
            return """You are a professional text analysis assistant specialized in analyzing science and engineering textbooks. Extract structured knowledge from chapters focusing on technical concepts, formulas, theorems, algorithms, and their logical relationships.

Node Types:
章节
小节
概念/定义
公式/定理/定律
算法/方法
实验/案例
应用场景

Relationship Types:
包含 (章节 → 小节)
组成 (小节 → 概念/公式/算法)
推导 (公式/定理之间的数学推导关系)
应用 (概念/公式 → 应用场景)
前提 (定理的前提条件)
结论 (定理的结论)
步骤 (算法/方法的执行步骤)
实例化 (概念 → 案例/实验)

Special Focus:
- Extract mathematical formulas, physical laws, and engineering principles
- Identify logical derivation chains (premise → theorem → conclusion)
- Capture algorithm flows and procedural steps
- Link theoretical concepts to practical applications
- Note experimental methods and case studies

Output Format (JSON Only, Chinese labels and descriptions):
{
  "nodes": [
    {
      "id": "1",
      "label": "概念1",
      "group": "类别1"
    }
  ],
  "edges": [
    {
      "from": "1",
      "to": "2",
      "label": "推导"
    }
  ]
}

ID Assignment Rules:
Existing chapter nodes use integer IDs ("1", "2", "3", etc.). Do not duplicate.
New subsections under existing chapters:
Chapter "1" subsections: "1.1", "1.2", "1.3", etc.
Chapter "2" subsections: "2.1", "2.2", "2.3", etc.
Continue similarly for other chapters.
Knowledge points, concepts, or formulas under subsections:
Under subsection "1.1": "1.1.1", "1.1.2", etc.
Under subsection "1.1.1": "1.1.1.1", "1.1.1.2", etc.
Continue similarly, maintaining a clear hierarchical structure.

Constraints:
Knowledge points extracted from the current chapter must not be isolated nodes. Each knowledge point must have at least one edge connecting it directly to a subsection or chapter node.

Final Checks:
1、Ensure all node IDs are unique.
2、"from" and "to" fields must reference existing node IDs.
3、Verify JSON structure correctness and completeness.
4、Pay special attention to formula-theorem relationships and algorithm flows.

Important: **DO NOT include any explanations or markdown formatting in the output.**
"""
        
        # 人文社科教材提示词
        elif textbook_type == "人文社科":
            return """You are a professional text analysis assistant specialized in analyzing humanities and social science textbooks. Extract structured knowledge focusing on theories, concepts, historical events, cultural phenomena, and their contextual relationships.

Node Types:
章节
小节
理论/学说
概念/术语
人物/学者
历史事件/案例
文化现象
观点/论点
研究方法

Relationship Types:
包含 (章节 → 小节)
组成 (小节 → 理论/概念)
提出 (人物 → 理论/观点)
影响 (理论/事件 → 影响对象)
发展 (理论/概念的历史发展脉络)
对比 (不同理论/观点的对比关系)
应用 (理论 → 研究方法/案例分析)
关联 (概念之间的语义关联)

Special Focus:
- Extract theoretical frameworks and schools of thought
- Identify key figures and their contributions
- Capture historical development and evolution of ideas
- Link concepts to cultural and social contexts
- Note comparative analyses and debates
- Highlight research methodologies and approaches

Output Format (JSON Only, Chinese labels and descriptions):
{
  "nodes": [
    {
      "id": "1",
      "label": "概念1",
      "group": "类别1"
    }
  ],
  "edges": [
    {
      "from": "1",
      "to": "2",
      "label": "影响"
    }
  ]
}

ID Assignment Rules:
Existing chapter nodes use integer IDs ("1", "2", "3", etc.). Do not duplicate.
New subsections under existing chapters:
Chapter "1" subsections: "1.1", "1.2", "1.3", etc.
Chapter "2" subsections: "2.1", "2.2", "2.3", etc.
Continue similarly for other chapters.
Knowledge points, concepts, or theories under subsections:
Under subsection "1.1": "1.1.1", "1.1.2", etc.
Under subsection "1.1.1": "1.1.1.1", "1.1.1.2", etc.
Continue similarly, maintaining a clear hierarchical structure.

Constraints:
Knowledge points extracted from the current chapter must not be isolated nodes. Each knowledge point must have at least one edge connecting it directly to a subsection or chapter node.

Final Checks:
1、Ensure all node IDs are unique.
2、"from" and "to" fields must reference existing node IDs.
3、Verify JSON structure correctness and completeness.
4、Pay attention to theoretical relationships and historical contexts.

Important: **DO NOT include any explanations or markdown formatting in the output.**
"""
        
        # 实际工作手册提示词
        elif textbook_type == "实际工作手册":
            return """You are a professional text analysis assistant specialized in analyzing practical work manuals and guides. Extract structured knowledge focusing on procedures, workflows, best practices, tools, and operational relationships.

Node Types:
章节
小节
流程/步骤
工具/方法
规范/标准
注意事项/要点
案例/示例
问题/解决方案
角色/职责

Relationship Types:
包含 (章节 → 小节)
组成 (流程 → 步骤)
使用 (工具 → 流程/方法)
遵循 (流程 → 规范/标准)
注意 (步骤 → 注意事项)
解决 (问题 → 解决方案)
示例 (概念 → 案例/示例)
负责 (角色 → 职责/流程)
前置 (步骤之间的先后顺序)

Special Focus:
- Extract operational procedures and workflows
- Identify tools, methods, and best practices
- Capture standards, regulations, and compliance requirements
- Link problems to solutions and troubleshooting steps
- Note practical examples and case studies
- Highlight roles, responsibilities, and organizational structures
- Emphasize critical points and common pitfalls

Output Format (JSON Only, Chinese labels and descriptions):
{
  "nodes": [
    {
      "id": "1",
      "label": "概念1",
      "group": "类别1"
    }
  ],
  "edges": [
    {
      "from": "1",
      "to": "2",
      "label": "包含"
    }
  ]
}

ID Assignment Rules:
Existing chapter nodes use integer IDs ("1", "2", "3", etc.). Do not duplicate.
New subsections under existing chapters:
Chapter "1" subsections: "1.1", "1.2", "1.3", etc.
Chapter "2" subsections: "2.1", "2.2", "2.3", etc.
Continue similarly for other chapters.
Knowledge points, procedures, or tools under subsections:
Under subsection "1.1": "1.1.1", "1.1.2", etc.
Under subsection "1.1.1": "1.1.1.1", "1.1.1.2", etc.
Continue similarly, maintaining a clear hierarchical structure.

Constraints:
Knowledge points extracted from the current chapter must not be isolated nodes. Each knowledge point must have at least one edge connecting it directly to a subsection or chapter node.

Final Checks:
1、Ensure all node IDs are unique.
2、"from" and "to" fields must reference existing node IDs.
3、Verify JSON structure correctness and completeness.
4、Pay attention to procedural flows and practical relationships.

Important: **DO NOT include any explanations or markdown formatting in the output.**
"""
        
        # 通用教材提示词（默认）
        else:
            return """You are a professional text analysis assistant tasked with analyzing a specific chapter from the textbook to extract Chapter, subsections, key concepts, knowledge points, and their relationships. Generate a knowledge graph structured as follows:
Node Types:
章节
小节
知识点
概念
公式/定理/算法

Relationship Types:
包含 (章节 → 小节)
组成 (小节 → 知识点/概念/公式)
先后 (时间或步骤顺序的知识点之间)
因果 (逻辑推导关系)

Output Format (JSON Only, Chinese labels and descriptions):
{
  "nodes": [
    {
      "id": "1",
      "label": "概念1",
      "group": "类别1"
    }
  ],
  "edges": [
    {
      "from": "1",
      "to": "2",
      "label": "包含"
    }
  ]
}

ID Assignment Rules:
Existing chapter nodes use integer IDs ("1", "2", "3", etc.). Do not duplicate.
New subsections under existing chapters:
Chapter "1" subsections: "1.1", "1.2", "1.3", etc.
Chapter "2" subsections: "2.1", "2.2", "2.3", etc.
Continue similarly for other chapters.
Knowledge points, concepts, or formulas under subsections:
Under subsection "1.1": "1.1.1", "1.1.2", etc.
Under subsection "1.1.1": "1.1.1.1", "1.1.1.2", etc.
Continue similarly, maintaining a clear hierarchical structure.

Constraints:
Knowledge points extracted from the current chapter must not be isolated nodes. Each knowledge point must have at least one edge ("包含" or "组成") connecting it directly to a subsection or chapter node.

Final Checks:
1、Ensure all node IDs are unique.
2、"from" and "to" fields must reference existing node IDs.
3、Verify JSON structure correctness and completeness.

Important: **DO NOT include any explanations or markdown formatting in the output.**
"""
    else:
        return  """
Please create a node with ID 0 as the **课程** node. Then, for each **章节** (chapter) node with IDs 1, 2, 3, and 4, generate a **"包含"** edge connecting them to the **课程** (textbook) node with ID 0.
Do NOT regenerate any nodes or edges that already exist in the provided input JSON graph. Specifically, the nodes and edges in the input JSON should remain unchanged. Only generate new nodes and edges to extend the graph based on the provided content.
Example:
Existing node:
Subsection: "id": "1", "label": "第1章", "group": "章节"
Subsection: "id": "2", "label": "第2章", "group": "章节"
Subsection: "id": "3", "label": "第3章", "group": "章节"
Subsection: "id": "4", "label": "第4章", "group": "章节"
From Chapter 1 to Chapter N And so on.

New nodes:
"id": "0", "label": "课程", "group": "教材"

New Edges:
{
  "from": "0",
  "to": "1",
  "label": "包含"
}
{
  "from": "0",
  "to": "2",
  "label": "包含"
}
{
  "from": "0",
  "to": "3",
  "label": "包含"
}
{
  "from": "0",
  "to": "4",
  "label": "包含"
}

Output Format (JSON Only, Chinese labels and descriptions):
{
  "nodes": [
    {
      "id": "1",
      "label": "概念1",
      "group": "类别1"
    }
  ],
  "edges": [
    {
      "from": "1",
      "to": "2",
      "label": "包含"
    }
  ]
}

Final Checks:

1、Ensure all node IDs are unique.
2、"from" and "to" fields must reference existing node IDs.
3、Verify JSON structure correctness and completeness.
4、Do NOT recreate existing nodes or edges in the input JSON.

Important: **DO NOT include any explanations or markdown formatting in the output.**
"""


def generate_graph_data(text, json_input=None, type="subgraph", textbook_type="通用"):
    """Call OpenAI API to generate graph nodes and edges data
    
    参数:
        text: 输入文本
        json_input: 已有的JSON图谱（可选）
        type: 图谱类型 ("subgraph" 或 "fullgraph")
        textbook_type: 教材类型 ("理工科", "人文社科", "实际工作手册", "通用")
    """

    # Detect the language of input text
    # language = detect_language(text)

    # Determine if we need to extend an existing graph
    is_extension = False
    if json_input:
        is_extension = True
        user_msg = "### 以下是已有知识图谱（JSON 格式），请在此基础上扩展 ###\n"
        user_msg += json_input
        user_msg = "\n\n### Please analyze the following text and generate relationship graph data: ###\n"
        user_msg += text
    else:
        user_msg = "### Please analyze the following text and generate relationship graph data: ###\n"
        user_msg += text
        
    # Get appropriate system prompt based on language, extension flag, and textbook type
    system_msg = get_system_prompt("chinese", is_extension, type, textbook_type)




    try:
        # Call OpenAI API
        # output = call_llm(system_msg, user_msg, st.session_state.current_model)

        # 使用侧边栏选择的模型，如果没有则使用默认模型
        model_name = st.session_state.get('current_model', '/mnt/chenbaiming/gpt-oss-120b')
        output = call_llm(system_msg, user_msg, model_name=model_name)

        if not output:
            raise ValueError("API returned empty response")
        
        # 确保output是字符串类型
        if not isinstance(output, str):
            raise ValueError(f"API returned non-string response: {type(output)}")

        # 检查是否是错误信息（API调用失败时返回的错误字符串）
        output_stripped = output.strip()
        if output_stripped.startswith("API call error:"):
            # 这是API调用错误，直接抛出异常，不要尝试解析JSON
            error_details = output_stripped.replace("API call error: ", "")
            raise ValueError(f"API调用失败: {error_details}")

        # Clean potential extra content from output
        output = output_stripped
        if output.startswith("```json"):
            output = output[7:]
        if output.endswith("```"):
            output = output[:-3]
        output = output.strip()

        # 再次检查清理后的output是否为空
        if not output:
            raise ValueError("API返回的内容为空，无法解析为JSON")

        # Parse JSON data
        result = json.loads(output)

        # Validate data format
        if not isinstance(result, dict):
            raise ValueError("Response is not a JSON object")
        if 'nodes' not in result or 'edges' not in result:
            raise ValueError("Missing required 'nodes' or 'edges' fields")
        if not isinstance(result['nodes'], list) or not isinstance(result['edges'], list):
            raise ValueError("'nodes' or 'edges' is not an array")
        # if len(result['nodes']) < 3:
        #     raise ValueError("At least 3 nodes are required")

        # Validate nodes and edges data
        node_ids = set()
        groups = set()
        for node in result['nodes']:
            if not all(k in node for k in ('id', 'label', 'group')):
                raise ValueError("Invalid node format - missing required fields")
            if not all(isinstance(node[k], str) for k in ('id', 'label', 'group')):
                raise ValueError("Node fields must be strings")
            if str(node['id']) in node_ids:
                raise ValueError(f"Duplicate node ID found: {node['id']}")
            node_ids.add(str(node['id']))
            groups.add(node['group'])

        for edge in result['edges']:
            if not all(k in edge for k in ('from', 'to', 'label')):
                raise ValueError("Invalid edge format - missing required fields")
            if not all(isinstance(edge[k], str) for k in ('from', 'to', 'label')):
                raise ValueError("Edge fields must be strings")
            # if str(edge['from']) not in node_ids:
            #     raise ValueError(f"Edge references non-existent source node: {edge['from']}")
            # if str(edge['to']) not in node_ids:
            #     raise ValueError(f"Edge references non-existent target node: {edge['to']}")

        # FIXME: removed the last two returnings
        return result['nodes'], result['edges']
        # return result['nodes'], result['edges'], system_msg, st.session_state.current_model


    except json.JSONDecodeError as je:
        # JSON解析错误
        st.error(f"❌ JSON解析失败: {str(je)}")
        st.error(f"API返回的原始内容: {output[:500]}...")  # 只显示前500个字符
        return [], []
    except ValueError as ve:
        # 值错误（包括API调用失败）
        error_msg = str(ve)
        if "API调用失败" in error_msg or "API returned" in error_msg:
            st.error(f"❌ {error_msg}")
            st.warning("💡 请检查：\n1. API密钥是否正确\n2. API账户是否可用\n3. 网络连接是否正常\n4. 模型名称是否正确")
        else:
            st.error(f"❌ 错误: {error_msg}")
        return [], []
    except Exception as e:
        # 其他未知错误
        st.error(f"❌ 生成知识图谱时出错: {str(e)}")
        import traceback
        st.error(f"详细错误信息:\n```\n{traceback.format_exc()}\n```")
        return [], []
