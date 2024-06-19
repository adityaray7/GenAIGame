#Townsfolks vs werewolves 

## Description
This is a fun simulation comprising of a mixture of mafia and among us. The villagers and werewolves are agents with seperate memories which are implemented using langchain. The Generative AI agents take decisions using opeai's LLM Model and decide to vote out suspicious villagers using their memories.

## Installation
1. Clone the repository to your local machine.
2. Navigate to the project directory: `/home/aditya/Documents/otsuka/game`.
3. Run the `requirements.py` script to install the dependencies:
    ```bash
    python requirements.py
    ```

## Usage
1. Create a virtual environment:
    - Linux:
      ```bash
      python3 -m venv venv
      source venv/bin/activate
      ```
    - Windows (PowerShell):
      ```powershell
      python -m venv venv
      .\venv\Scripts\Activate.ps1
      ```

2. Install the project dependencies:
    ```bash
    pip install -r requirements.txt    
    ```

3. Initialize the environment variables by creating a `.env` file based on the provided `.env.example` file.
    ```bash
    cp .env.example .env
    ```

4. Run the game:
    ```bash
    python game.py
    ```

## Contributing
We welcome contributions! If you'd like to contribute to the project, please follow these steps:
1. Fork the repository.
2. Create a new branch for your feature or bug fix.
3. Make your changes and commit them.
4. Push your changes to your forked repository.
5. Submit a pull request to the main repository.

