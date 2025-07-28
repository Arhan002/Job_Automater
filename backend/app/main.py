# main.py

from fastapi import FastAPI

# Create an instance of the FastAPI class
app = FastAPI()

# Define a "path operation decorator"
@app.get("/")
def read_root():
    # Return a dictionary, which FastAPI will automatically convert to JSON
    return {"message": "Hello, World"}
