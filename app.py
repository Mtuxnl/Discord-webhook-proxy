import os
import datetime
import markdown
import requests
import json
import logging
import base64
from flask import Flask, request, render_template, jsonify
from jinja2 import DictLoader
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()

app = Flask(__name__)

OUTGOING_WEBHOOK_BASE_URL = os.getenv('OUTGOING_WEBHOOK_BASE_URL')
MEDIA_PROXY_HOST = os.getenv('MEDIA_PROXY_HOST', 'assets.mtux.nl') 
MEDIA_PROXY_URL_BASE = f"https://{MEDIA_PROXY_HOST}/_matrix/media/r0/download/{MEDIA_PROXY_HOST}"

if not OUTGOING_WEBHOOK_BASE_URL:
    logger.warning("LET OP: OUTGOING_WEBHOOK_BASE_URL is niet ingesteld!")

webhook_data_store = {}

# --- Templates ---
BASE_TEMPLATE = """
<!DOCTYPE html>
<html lang="nl">
<head><title>Hookshot Proxy</title>
<style>body{background:#36393f;color:#dcddde;font-family:sans-serif;padding:20px}code{background:#2f3136}</style>
</head><body>{% block content %}{% endblock %}</body></html>
"""
HOME_TEMPLATE = """{% extends "base.html" %}{% block content %}<h1>Proxy Running</h1>{% endblock %}"""

app.jinja_loader = DictLoader({'base.html': BASE_TEMPLATE, 'home.html': HOME_TEMPLATE})

def markdown_to_html(text):
    if not text: return ""
    return markdown.markdown(text, extensions=['fenced_code', 'nl2br'])

def discord_color_to_hex(color_int):
    if not color_int: return "#f0ad4e" 
    return "#{:06x}".format(color_int)

def proxify_image_url(original_url):
    if not original_url: return ""
    try:
        encoded = base64.urlsafe_b64encode(original_url.encode('utf-8')).decode('utf-8').rstrip('=')
        return f"{MEDIA_PROXY_URL_BASE}/url_{encoded}"
    except Exception:
        return original_url

def format_discord_to_matrix(data):
    parts_html = []
    parts_text = []

    # 1. Content (Boven de embed)
    content = data.get('content', '')
    if content:
        parts_text.append(content)
        parts_html.append(markdown_to_html(content))

    # 2. Embeds verwerken
    for embed in data.get('embeds', []):
        color_hex = discord_color_to_hex(embed.get('color'))
        
        # --- BLOCKQUOTE (De 'Card' Container) ---
        embed_html = (
            f'<blockquote style="border-left: 4px solid {color_hex}; '
            f'background-color: #2f3136; '
            f'padding: 10px; '
            f'margin: 5px 0; '
            f'border-radius: 0 4px 4px 0;">'
        )
        embed_text = "\n--- Embed ---\n"

        thumb_url = proxify_image_url(embed.get('thumbnail', {}).get('url'))
        image_url = proxify_image_url(embed.get('image', {}).get('url'))

        # --- LINKER KOLOM CONTENT ---
        left_html = ""

        # Author
        if 'author' in embed:
            name = embed['author'].get('name', '')
            if name:
                embed_text += f"{name}\n"
                left_html += f"<strong>{name}</strong><br>"

        # Title
        if 'title' in embed:
            title = embed.get('title', '')
            url = embed.get('url')
            embed_text += f"{title}\n"
            link = f"<a href='{url}' style='color:#00b0f4; text-decoration:none; font-size:1.1em; font-weight:bold;'>{title}</a>" if url else f"<strong>{title}</strong>"
            left_html += f"{link}<br>"

        # Description
        if 'description' in embed:
            desc = embed.get('description', '')
            embed_text += f"{desc}\n"
            left_html += f"<div style='color:#dcddde; margin-top:4px; margin-bottom:8px;'>{markdown_to_html(desc)}</div>"

        # Fields
        if 'fields' in embed:
            for field in embed['fields']:
                name = field.get('name', '')
                value = field.get('value', '')
                embed_text += f"{name}: {value}\n"
                left_html += f"<div style='margin-bottom:2px;'><span style='color:#ffffff; font-weight:bold;'>{name}</span>: <span style='color:#dcddde;'>{markdown_to_html(value)}</span></div>"

        # --- TABEL LAYOUT ---
        embed_html += '<table width="100%" border="0" cellspacing="0" cellpadding="0" style="background-color:#2f3136; border:none; border-collapse:collapse;">'
        embed_html += '<tr style="background-color:#2f3136; border:none;">'
        
        # Kolom 1: Tekst (Links)
        embed_html += f'<td valign="top" style="padding-right: 15px; border:none; background-color:#2f3136; color:#dcddde;">{left_html}</td>'
        
        # Kolom 2: Poster (Rechts)
        if thumb_url:
            embed_html += '<td valign="top" width="120" style="border:none; background-color:#2f3136;">'
            embed_html += f'<img src="{thumb_url}" width="120" style="border-radius:4px;" alt="Poster">'
            embed_html += '</td>'
        
        embed_html += '</tr></table>'

        # --- LARGE IMAGE (Backdrop) ---
        if image_url:
            embed_text += f"[Image: {image_url}]\n"
            embed_html += f'<div style="margin-top:12px;"><img src="{image_url}" width="100%" style="border-radius:4px;" alt="Backdrop"></div>'

        # Footer
        if 'footer' in embed:
            ft = embed['footer'].get('text', '')
            if ft:
                embed_text += f"Footer: {ft}\n"
                embed_html += f"<br><small style='color:#72767d;'>{ft}</small>"

        embed_html += "</blockquote>"
        
        parts_html.append(embed_html)
        parts_text.append(embed_text)

    final_html = "".join(parts_html)
    final_text = "\n".join(parts_text) or "Empty message"
    
    if not final_html: final_html = "<i>Empty message</i>"

    return {
        "username": data.get('username', 'Arr Bot'),
        "avatar_url": proxify_image_url(data.get('avatar_url')),
        "text": final_text,
        "html": final_html
    }

def send_to_hookshot(webhook_id, payload):
    if not OUTGOING_WEBHOOK_BASE_URL: return
    base = OUTGOING_WEBHOOK_BASE_URL.rstrip('/')
    target_url = f"{base}/{webhook_id}"
    try:
        requests.post(target_url, json=payload, headers={'Content-Type': 'application/json'}, timeout=15)
    except Exception as e:
        logger.error(f"Hookshot error: {e}")

@app.route('/')
def list_webhooks():
    return render_template('home.html', webhooks=webhook_data_store, base_url=OUTGOING_WEBHOOK_BASE_URL)

@app.route('/webhook/<webhook_id>', methods=['POST'])
def receive_webhook(webhook_id):
    if not request.is_json: return jsonify({"error": "JSON required"}), 400
    data = request.json
    webhook_data_store[webhook_id] = {"received_at": datetime.datetime.now().strftime('%H:%M:%S')}
    payload = format_discord_to_matrix(data)
    send_to_hookshot(webhook_id, payload)
    return jsonify({"status": "processed"}), 200

if __name__ == '__main__':
    from waitress import serve
    print("Proxy active on 5001")
    serve(app, host='0.0.0.0', port=5001)
