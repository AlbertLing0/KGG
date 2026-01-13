from fastapi import FastAPI
from pydantic import BaseModel
from utils import generate_graph_data  # 你已有的图谱生成函数
from fastapi.responses import JSONResponse
from datetime import datetime

from threading import Thread

import threading
import time
from pydantic import BaseModel, Field
from docx import Document
from fastapi import File, UploadFile

from io import BytesIO

import uuid

from word_graph.word_graph import split_into_chapters, generate_subgraph_for_chapters, merge_subgraphs, parse_and_merge_json_input

app = FastAPI()

class GraphRequest(BaseModel):
    text_input: str
    json_input: str = None  # 可选
    type: str  # "subgraph" or "fullgraph"

class GenerateRequest(BaseModel):
    id:str
    status:str
    process:object = Field(..., exclude=True)
    result:object = None
    accessed:bool = Field(..., exclude=True)
    clean_base:datetime = Field(..., exclude=True)

    @classmethod
    def create(cls):
        return cls(
            id=str(uuid.uuid1()),
            status="processing",
            process=None,
            accessed=False,
            clean_base=datetime.now()
        )
    
    def set_done(self):
        self.clean_base = datetime.now()
        self.status = "done"

    def set_error(self):
        self.clean_base = datetime.now()
        self.status = "error"

WRITE_MUTEX = threading.Lock()

REQUEST_MAP = {}
ACCESSED_REQUEST_EXPIRE_SECONDS = 60
NON_ACCESSED_REQUEST_EXPIRE_SECONDS = 300
ERRORED_REQUEST_EXPIRE_SECONDS = 120
PROCESS_TIME_OUT_SECONDS = 600
CLEAN_UP_INTERVAL_SECONDS = 300

@app.post("/generate-graph")
async def generate_graph(graph_request: GraphRequest):
    try:
        request:GenerateRequest = GenerateRequest.create()
        def process_function():
            try:
                # 调用图谱生成逻辑
                print(f'generating graph...(id: {request.id})')
                nodes, edges = generate_graph_data(
                    graph_request.text_input,
                    graph_request.json_input,
                    graph_request.type)
                
                print(f'generated (id: {request.id})')
                
                request.result = {
                    'nodes': nodes,
                    'edges': edges
                }
                request.set_done()
            except Exception as e:
                print(f"error: {e}")
                request.set_error()

        process = Thread(target=process_function, daemon=True)
        request.process = process

        request.process.start()
        
        WRITE_MUTEX.acquire()
        REQUEST_MAP[request.id] = request
        WRITE_MUTEX.release()

        return JSONResponse(content=request.model_dump())

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

@app.post("/generate-graph-file")
async def generate_graph(file: UploadFile = File(...)):
    content = await file.read()
    bytesIO = BytesIO(content)
    
    try:
        request:GenerateRequest = GenerateRequest.create()
        def process_function():
            try:
                # 调用图谱生成逻辑
                print(f'generating graph...(id: {request.id})')

                doc = Document(bytesIO)
                text = "\n".join([para.text for para in doc.paragraphs])
                chapters = split_into_chapters(text)
                subgraphs = generate_subgraph_for_chapters(chapters)
                graph = merge_subgraphs(subgraphs)
                with open(graph, "r", encoding="utf-8") as f:
                    graph_json = f.read()
                end_nodes, end_edges = parse_and_merge_json_input(graph_json)

                print(f'generated (id: {request.id})')
                
                request.result = {
                    'nodes': end_nodes,
                    'edges': end_edges
                }
                request.set_done()
            except Exception as e:
                print(f"error: {e}")
                request.set_error()

        process = Thread(target=process_function, daemon=True)
        request.process = process

        request.process.start()
        
        WRITE_MUTEX.acquire()
        REQUEST_MAP[request.id] = request
        WRITE_MUTEX.release()

        return JSONResponse(content=request.model_dump())

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )


@app.get("/query")
async def query(id:str):
    request:GenerateRequest = REQUEST_MAP[id]
    
    if request is None:
        return JSONResponse(
            status_code=404,
            content={"error": f"the request you're quering: {id} doesn't exist or is expired"}
        )
    
    return JSONResponse(
        status_code=200,
        content=request.model_dump()
    )
    
def clean_up_thread_main():
    time.sleep(CLEAN_UP_INTERVAL_SECONDS)
    WRITE_MUTEX.acquire()
    try:
        now = datetime.now()

        for raw_request in REQUEST_MAP.items():
            request: GenerateRequest = raw_request
            time_diff = now - request.clean_base
            if request.status == 'processing':
                if time_diff.seconds > PROCESS_TIME_OUT_SECONDS:
                    # wait for next turn to clean up
                    # let the frontend know this request has failed
                    request.set_error()
                    
            elif request.status == 'success':
                if request.accessed and time_diff.seconds > ACCESSED_REQUEST_EXPIRE_SECONDS:
                    REQUEST_MAP.pop(request.id)
                elif not request.accessed and time_diff.seconds > NON_ACCESSED_REQUEST_EXPIRE_SECONDS:
                    REQUEST_MAP.pop(request.id)

            elif request.status == 'error' and time_diff.seconds > ERRORED_REQUEST_EXPIRE_SECONDS:
                REQUEST_MAP.pop(request.id)
    except Exception as e:
        print(f'Error when cleaning up requests: {e}')
        print('Dont worry, lock will be released but please check the exception')
    finally:
        WRITE_MUTEX.release()

CLEAN_UP_THREAD = threading.Thread(
    target=clean_up_thread_main,
    daemon=True)

if __name__ == '__main__':
    import uvicorn
    CLEAN_UP_THREAD.start()
    uvicorn.run(app, host="0.0.0.0", port=25565)
