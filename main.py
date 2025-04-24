from fastapi import FastAPI, Request
from pydantic import BaseModel
from utils import generate_graph_data  # 你已有的图谱生成函数
from fastapi.responses import JSONResponse, FileResponse
import json
import os
from datetime import datetime

app = FastAPI()

class GraphRequest(BaseModel):
    text_input: str
    json_input: str = None  # 可选
    type: str  # "subgraph" or "fullgraph"

@app.post("/generate-graph")
async def generate_graph(request: GraphRequest):
    try:
        # 调用图谱生成逻辑
        nodes, edges = generate_graph_data(
            request.text_input,
            request.json_input,
            request.type
        )

        # 构建输出结构
        output = {
            "nodes": nodes,
            "edges": edges
        }

        return JSONResponse(content=output)

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=25565)