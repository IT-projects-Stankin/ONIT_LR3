import html
import logging
import os
import socket
from contextlib import asynccontextmanager
import psycopg
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("guestbook")
DATABASE_URL = os.environ["DATABASE_URL"]
APP_VERSION = os.environ.get("APP_VERSION", "dev")
HOSTNAME = socket.gethostname()
PAGE = '<!doctype html>\n<html lang="ru">\n<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">\n<title>Гостевая книга</title>\n<style>\nbody {font:16px/1.5 Arial,sans-serif; background:#f5f6f7; color:#232a31; margin:0;}\nmain {max-width:690px; margin:50px auto; padding:28px; background:white; border:1px solid #ddd; border-radius:8px;}\nh1 {margin:0 0 3px;} p {color:#67727c;} form {display:flex; gap:10px; margin:26px 0;}\ninput {flex:1; min-width:0; border:1px solid #aaa; border-radius:5px; padding:12px; font:inherit;}\nbutton {background:#245b82; color:white; padding:11px 16px; border:0; border-radius:5px; cursor:pointer;}\nul {padding:0; list-style:none;} li {padding:12px; background:#f5f6f7; margin:8px 0; border-radius:5px;}\nsmall {color:#6a7680;}\n</style>\n</head><body><main><h1>Гостевая книга</h1>\n<p>Оставьте сообщение — оно сохранится в общей базе.</p>\n<form method="post" action="/messages"><input name="text" placeholder="Ваше сообщение" required maxlength="500"><button type="submit">Отправить</button></form>\n<h2>Сообщения</h2><ul><!--ITEMS--></ul><small>Версия <!--VERSION--> · ответила реплика <!--HOST--></small></main></body></html>'


def init_db():
    with psycopg.connect(DATABASE_URL) as conn:
        conn.execute("SELECT pg_advisory_xact_lock(42)")
        conn.execute("""CREATE TABLE IF NOT EXISTS messages (
            id SERIAL PRIMARY KEY,
            text TEXT NOT NULL,
            created_at TIMESTAMPTZ DEFAULT now()
        )""")


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(lifespan=lifespan)

@app.middleware("http")
async def replica_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Served-By"] = HOSTNAME
    response.headers["X-App-Version"] = APP_VERSION
    return response


@app.get("/", response_class=HTMLResponse)
def index():
    with psycopg.connect(DATABASE_URL) as conn:
        rows = conn.execute("SELECT text FROM messages ORDER BY id DESC").fetchall()
    items = "".join("<li>" + html.escape(row[0]) + "</li>" for row in rows)
    return (PAGE.replace("<!--ITEMS-->", items)
                .replace("<!--VERSION-->", html.escape(APP_VERSION))
                .replace("<!--HOST-->", html.escape(HOSTNAME)))


@app.post("/messages")
def add_message(request: Request, text: str = Form(...)):
    with psycopg.connect(DATABASE_URL) as conn:
        conn.execute("INSERT INTO messages (text) VALUES (%s)", (text,))
    log.info("Сообщение от %s: %s", request.headers.get("x-real-ip"), text)
    return RedirectResponse("/", status_code=303)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/version")
def version():
    return {"version": APP_VERSION, "host": HOSTNAME}
