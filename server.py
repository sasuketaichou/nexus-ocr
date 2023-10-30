from fastapi import FastAPI, File, UploadFile
import json

from preprocessed import execute
from main import file_dct, templates

app = FastAPI()

@app.post("/extract/")
async def extract(file: UploadFile = File(...)):
    filename = file.filename
    filetype = filename.split('.')[-1]

    if filetype in ['jpg', 'jpeg', 'JPG', 'pdf']:

        result = execute(filename, templates, file_dct)
        return result
    return {"message": "Invalid file type"}