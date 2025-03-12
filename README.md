## QIFatron / QIFtronics

A collection of .QIF (quality information framework) tools  with a pretty bland but useful web interface. For forensic stuff - useful when transitioning to GD&T in PMI / DX stuff

  - qif diff
  - xml validation
  - qif validation
  - qif visualisation
  - PMI annotation search

## Setup

```
cd app/
npm install
cd ..
python -m venv venv 
source venv/bin/requirements
pip install -r requirements
python app.py
```

```
# windows I think sourcing the venv is the only difference
\venv\Scripts\Activate.ps1 
```


## Tailwind Node Changes

```
npx tailwindcss -i ./static/css/style.css -o ./static/css/output.css --watch
```
