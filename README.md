# AISC Steel Checker PRO

A Streamlit-based preliminary steel design checker for:
- beams
- columns
- braces
- beam-columns

## Main features
- LRFD / ASD switch
- AISC-style axial, flexural, shear, and interaction checks
- optional seismic / Zone 4 compactness screening
- wide flange, HSS rectangular, HSS round, pipe, and circular tubular support
- simple major-axis LTB screening for W sections
- conceptual strong-column / weak-beam panel
- batch checking through CSV upload
- Excel export of results

## Files
- `app.py`
- `requirements.txt`
- `sample_batch.csv`
- `sample_sections_office_format.csv`

## Run
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Important limitation
This is a preliminary office checker. It does not yet replace:
- full frame analysis
- complete AISC 341 detailing
- connection design
- panel zone checks
- brace/gusset design
- story drift verification from global model
- formal NSCP seismic workflow
