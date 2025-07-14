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

## Usage

Start the server using `./start_server.sh`

The server should be hosted locally on port 5000

Use the provided shell scripts to test the endpoints.