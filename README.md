# ai-notebook-server

Simple server to interface with our AI Notebook Model

## Installation

1. Clone the repository `git clone https://github.com/daniel-theunissen/ai-notebook-server.git`
2. Install dependencies in a new virtual environment
```
pip install pandas
pip install numpy
pip install flask
pip install pipenv
pip install python-dotenv
pip install openai
```
3. Install PyTorch for your platform

[Instructions here](https://pytorch.org/get-started/locally/)

4. Install the Sentence Transformers module
```
pip install "transformers[torch]"
pip install -U sentence-transformers
```


## Usage

Start the server using `./start_server.sh`

The server should be hosted locally on port 5000

Store a new note using `./add_note "<note>"`

Query the database using `./ask_question "<question>"`
