## QIFATRON

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
