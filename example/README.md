1.Install Dependencies (Local): Generate uv.lock and install dependencies:
uv lock
uv sync
1. Build and Run Docker Container:
docker-compose up --build
2. Test with Client: Run the client script:   
uv run --active python client.py