# CITS3403 Group Project
2025 Agile Web Development Project

## Purpose
This web application is a trade journal platform for day traders, providing tools to log, analyze, and reflect on trades. The app enables users to record trade details, upload profit/loss data, and attach up to five images per trade for visual review. Users can tag trades with emotions and rule-following status, helping them identify patterns in their trading behavior and decision-making.

The platform emphasizes self-improvement through structured journaling, allowing traders to track their progress, learn from both successful and unsuccessful trades, and refine their strategies over time. The tagging and analytics features help users evaluate adherence to trading plans, and adapt to changing market conditions.

Additionally, the app includes a social feature where users can generate and share monthly profit summaries as images, fostering friendly competition and motivation within their trading networks. By providing a clear, organized, and emotion-free space for trade review, the journal supports traders in building discipline, confidence, and consistent performance.

## Design and Use of Application

The application is built using Flask for the backend and HTML/CSS/JavaScript for the frontend. Users can register and log in to access their personal trade journals. The main dashboard provides an overview of recent trades and key statistics.

**Key Features:**
- **Trade Logging:** Users can add new trades by entering details such as date, ticker, entry/exit points, profit/loss, and notes. Up to five images (e.g., charts or screenshots) can be attached to each trade.
- **Analytics:** The app provides visualizations and summaries, such as monthly profit charts, win/loss ratios, and most common emotional tags.
- **Social Sharing:** Users can generate monthly summary images and share them with others to encourage accountability and motivation.
- **Trade Review:** Users can filter and search past trades, making it easy to review performance and identify patterns.

The intuitive interface is designed for quick data entry and easy navigation, supporting traders in building consistent habits and improving their strategies over time.

## Group Members

| UWA ID   | Name           | Github Username |
| -------- | -------------- | --------------- |
| 23876554 | Rory Cusworth  | rozza368        |
| 22879249 | Sina Shahrivar | Sina-Jeff       |
| 23421575 | Jared Huynh    | Jarednhu        |
| 23593643 | Michael Allen  | Michaelallen5   |

## Setup

**First, create a Python virtual environment and source it:**

On Linux:
```bash
python3 -m venv application-env
source application-env/bin/activate
```

On Windows:

1. **Open a terminal and navigate to the project folder:**
   ```powershell
   cd cits3403-group-project
   ```

2. **Create and activate a Python virtual environment:**
   ```powershell
   py -m venv application-env
   .\application-env\Scripts\activate
   ```

3. **Install required packages:**
   ```powershell
   pip install -r requirements.txt
   ```

4. **Run the server:**
   ```powershell
   flask --app main.py run
   ```

> **Note:**  
> Make sure you are in the `cits3403-group-project` directory (where `requirements.txt` and `main.py` are located) before running the install and server commands.

## Running Tests

On Linux:

1. Make sure your virtual environment is activated:
   ```bash
   source application-env/bin/activate
   ```
2. From the project root directory, run:
   ```bash
   python -m unittest discover -s test
   ```
This will automatically discover and run all tests in the `test` folder.

On Windows

1. Make sure your virtual environment is activated:
   ```powershell
   .\application-env\Scripts\activate
   ```
2. From the project root directory, run:
   ```powershell
   python -m unittest discover -s test
   ```
This will automatically discover and run all tests in the `test` folder.

## Acknowledgement

This project utilised AI tools such as ChatGPT and Github Copilot to assist with its creation.