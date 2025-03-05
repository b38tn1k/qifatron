## LOCAL PORTAL

## Tailwind Node Changes

```
npx tailwindcss -i ./static/css/style.css -o ./static/css/output.css --watch
```

## TMUX
Keeps the development server alive even when I am logged out

```
tmux new -s flask_server

to detach: Ctrl+B, the D

to reattach:
tmux attach -t flask_server
```
