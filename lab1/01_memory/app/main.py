import html
import logging
from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse, RedirectResponse

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("guestbook")
app = FastAPI()
messages = []  # Часть 1: список находится только в памяти процесса.
PAGE = '<!doctype html>\n<html lang="ru">\n<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">\n<title>Гостевая книга</title>\n<style>\nbody {font:16px/1.5 Arial,sans-serif; background:#f5f6f7; color:#232a31; margin:0;}\nmain {max-width:690px; margin:50px auto; padding:28px; background:white; border:1px solid #ddd; border-radius:8px;}\nh1 {margin:0 0 3px;} p {color:#67727c;} form {display:flex; gap:10px; margin:26px 0;}\ninput {flex:1; min-width:0; border:1px solid #aaa; border-radius:5px; padding:12px; font:inherit;}\nbutton {background:#245b82; color:white; padding:11px 16px; border:0; border-radius:5px; cursor:pointer;}\nul {padding:0; list-style:none;} li {padding:12px; background:#f5f6f7; margin:8px 0; border-radius:5px;}\nsmall {color:#6a7680;}\n</style>\n</head><body><main><h1>Гостевая книга</h1>\n<p>Оставьте сообщение, и оно появится в списке.</p>\n<form method="post" action="/messages"><input name="text" placeholder="Ваше сообщение" required maxlength="500"><button type="submit">Отправить</button></form>\n<h2>Сообщения</h2><ul><!--ITEMS--></ul><small>Лабораторная работа № 1. Основы новых интернет-технологий.</small></main></body></html>'


@app.get("/", response_class=HTMLResponse)
def index():
    items = "".join("<li>" + html.escape(m) + "</li>" for m in reversed(messages))
    return PAGE.replace("<!--ITEMS-->", items)


@app.post("/messages")
def add_message(text: str = Form(...)):
    messages.append(text)
    log.info("Добавлено сообщение: %s", text)
    return RedirectResponse("/", status_code=303)


@app.get("/health")
def health():
    return {"status": "ok"}
