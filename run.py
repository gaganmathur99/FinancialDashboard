import uvicorn

if __name__ == "__main__":
    # Start the server with hot reloading for development
    uvicorn.run(
        "backend.app.main:app", 
        host="0.0.0.0", 
        port=5000, 
        reload=True
    )