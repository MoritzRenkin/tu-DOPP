# Natural Disaster Trends
This repository and the data and code it contains aims to analyze trends in natural disasters occurences and their impact, as well as their possible correlation with global warming. The analysis is primarly based on the Emergency Events Database (EM-DAT) created by the Centre for Research on the Epidemiology of Disasters (CRED).

The project addresses the following questions:
- How did the number of deaths per year from natural disasters change over the last years?
- How does this vary by country? How does this vary by type of natural disaster?
- Are there trends visible that could be due to Global Warming?

## Setup
The project is embedded in a jupyter notebook with Python 3.8+. Before running it, install the required packages in ´requirements.txt´ first (preferably in a virtual environment). 
Using pip on Windows:
```
py -3 -m pip install -r requirements.txt
```
Using pip on Un*x or MacOS:
```
python3 -m pip install -r requirements.txt
```
Using Conda:
```
conda install --yes --file requirements.txt
```

## Running the code

Start Jupyter Notebook and open `jupyter_notebooks/Full_analysis.ipynb` to run the code yourself.

## Folder Structure

`data/`: Contains the different input datasets used in the analysis as well as the transformed `output df_transformed.csv`
`jupyter_notebooks/`: Contains the Jupyter notebooks used for data processing and analysis.
`graphics/`: Contains external copies from the visulizations inside `jupyter_notebooks/Full_analysis.ipynb`.
