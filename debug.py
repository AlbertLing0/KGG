from word_graph.word_graph import parse_and_merge_json_input

path:str = 'json_data/full_knowledge_graph_2025-05-06_08-43-11.json'

with open(path, 'r', encoding='utf-8') as f:
    graph_json = f.read()

end_nodes, end_edges = parse_and_merge_json_input(graph_json)

