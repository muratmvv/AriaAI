# Aria - Autonomous System Assistant

Aria is a personal artificial intelligence assistant capable of performing autonomous operations within a local computing environment, processing voice commands, and operating through a modern web interface.

This project was developed to explore how an artificial intelligence can go beyond simple text generation—actively managing files, writing and testing code, executing terminal commands, and conducting research on the web independently.

## System Architecture

The project consists of two primary components:

1. Backend (Python / FastAPI): Handles the assistant's decision-making logic, autonomous tools, and AI model integrations.
2. Frontend (React / Vite): Provides a modern, dark-themed user interface along with experimental browser-based features such as camera and hand gesture tracking.

## Core Capabilities

- Autonomous Execution Loop: Analyzes given commands, selects the appropriate tools, executes them, and evaluates the results.
- System Control: Executes commands via PowerShell and monitors hardware resources including CPU, RAM, and disk usage.
- Code Management: Generates, writes, and tests scripts independently in Python and other languages.
- Communication: Supports text-based interaction alongside advanced voice synthesis and processing capabilities.

## Setup and Installation

Follow these steps to run the project locally.

### 1. Clone the Repository
git clone https://github.com/muratmvv/AriaAI.git
cd AriaAI

### 2. Backend (Python) Setup
Install the required dependencies and configure the environment:
pip install -r requirements.txt

Create a `.env` file in the root directory and define your API credentials:
API_BASE_URL=https://api.groq.com/openai/v1
API_KEY=your_api_key_here
MODEL_NAME=qwen/qwen3.8-27b

Start the Python API server:
python server.py

### 3. Frontend (React) Setup
Open a new terminal window, navigate to the interface directory, and run the development server:
cd aria-ui
npm install
npm run dev

Access the user interface via the local link provided in your browser.
