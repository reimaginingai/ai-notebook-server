# ai-notebook-server

Simple server to interface with our AI Notebook Model

## Installation

### Local
1. Clone the repository `git clone https://github.com/daniel-theunissen/ai-notebook-server.git`
2. Install dependencies in a new virtual environment
```
pip install -r requirements.txt
```
3. Install PyTorch for your platform

[Instructions here](https://pytorch.org/get-started/locally/)

4. Install the Sentence Transformers module
```
pip install "transformers[torch]"
pip install -U sentence-transformers
```

5. Set your environment variables
```
PRIVATE_KEY={your firebase database key}
```

### Docker
1. Log into ghcr 
```
docker login ghcr.io -u <USERNAME> -p <PERSONAL_ACCESS_TOKEN>
```

2. Pull the container
```
docker pull ghcr.io/daniel-theunissen/notebook-ai-api
```

3. Create `.env` containing:
```
PRIVATE_KEY={your firebase database key}
``` 

## Usage

### Local

Start the server using `./start_server.sh`

The server should be hosted locally on port 5000

Use the provided shell scripts to test the endpoints.

### Docker

Start the server by running the container:

```
docker run -d \
    --name notebook-ai-api \
    -p 5000:5000 \
    --gpus all \
    --env-file .env \
    ghcr.io/daniel-theunissen/notebook-ai-api
```
