# Clinical Trials Analysis
This project analyzes clinical trial data to identify trends.

## Installation
1. Clone the repo:

git clone https://github.com/your-username/upwork-clin-trials.git

2. Install dependencies:
pip install -r requirements.txt

## Usage
Run the analysis:
python src/analyze.py
Results will be saved in the `results/` folder.

3. Pull data from clinicaltrials.gov using the API and store into a DB called UW_clin_trials.db
python3 src/api-call-clinical-trials.py

4. Process raw data from the DB and produce a streamlit app
python3 src/create-streamlit.app.py
