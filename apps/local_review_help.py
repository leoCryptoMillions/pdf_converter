"""Shared, local help content for FAQ, guide and contextual explanations."""
from __future__ import annotations

import html
import json
import unicodedata
from pathlib import Path

ASSETS = Path(__file__).with_name("local_review_assets")
TOPICS = json.loads((ASSETS / "help.json").read_text(encoding="utf-8"))


def help_link(topic: str) -> str:
    title = html.escape(TOPICS[topic]["title"], quote=True)
    return (f'<a class="context-help" href="/ayuda#topic-{topic}" '
            f'data-help-topic="{topic}" aria-label="Ayuda: {title}" '
            f'title="Ayuda: {title}"><span aria-hidden="true">?</span></a>')


def mascot(size: int = 112) -> str:
    return (f'<span class="mascot"><img src="/assets/pdf-converter-guide.png" '
            f'width="{size}" height="{size}" alt="PDF Converter, tu guía de ayuda" '
            'decoding="async"></span>')


def contextual_templates() -> str:
    return "".join(
        f'<template id="help-topic-{key}" data-title="{html.escape(topic["title"], quote=True)}">'
        + "".join(f'<p>{html.escape(paragraph)}</p>' for paragraph in topic["paragraphs"])
        + '</template>'
        for key, topic in TOPICS.items()
    )


def normalize(text: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", text.lower())
                   if unicodedata.category(c) != "Mn")


def render_help(query: str = "") -> str:
    term = normalize(query.strip())
    categories: dict[str, list[str]] = {}
    category_matches: dict[str, bool] = {}
    count = 0
    for key, topic in TOPICS.items():
        # Action explanations without an FAQ question remain deep-linkable.
        question = topic.get("question", topic["title"])
        answer = "".join(f'<p>{html.escape(p)}</p>' for p in topic["paragraphs"])
        matches = not term or term in normalize(question + " " + " ".join(topic["paragraphs"]))
        if topic.get("question"):
            count += int(matches)
            category_matches[topic["category"]] = category_matches.get(topic["category"], False) or matches
            categories.setdefault(topic["category"], []).append(
                f'<details class="faq-item" id="topic-{key}" data-faq-item '
                f'{"open" if term and matches else ""} {"hidden" if not matches else ""}>'
                f'<summary>{html.escape(question)}</summary><div class="faq-answer">{answer}</div></details>'
            )
    faq_html = "".join(
        f'<section class="faq-category" data-faq-category {"" if category_matches[category] else "hidden"}><h3>{html.escape(category)}</h3>'
        + "".join(items) + '</section>' for category, items in categories.items()
    )
    action_help = "".join(
        f'<details class="faq-item" id="topic-{key}"><summary>{html.escape(topic["title"])}</summary>'
        '<div class="faq-answer">' + "".join(f'<p>{html.escape(p)}</p>' for p in topic["paragraphs"])
        + '</div></details>'
        for key, topic in TOPICS.items() if not topic.get("question")
    )
    return f"""
<div class="help-hero">
  {mascot(192)}
  <div><p class="eyebrow">UN POCO DE AYUDA, MUCHAS POSIBILIDADES</p>
    <h1>Vamos paso a paso.</h1>
    <p>Soy PDF Converter, tu guía para convertir y revisar tus documentos.</p>
    <p class="hint">Encuentra una respuesta o sigue la guía para empezar.</p></div>
</div>
<div class="help-layout">
  <nav class="panel help-toc" aria-label="En esta ayuda">
    <h2>Centro de ayuda</h2>
    <a href="#faq">Preguntas frecuentes</a><a href="#guia">Guía de uso</a><a href="#acciones">Ayuda de las acciones</a>
    <div class="action-with-help"><a class="secondary-button" href="/" data-help-action="new">Ir al convertidor</a>{help_link('new')}</div>
  </nav>
  <div class="help-content">
    <section id="faq" class="panel help-section" aria-labelledby="faq-title">
      <h2 id="faq-title">Preguntas frecuentes</h2><p class="hint">Respuestas sobre archivos, formatos, OCR y resultados.</p>
      <form action="/ayuda#faq" method="get" id="faq-search-form" class="faq-search-form">
        <label class="field-label" for="faq-search">Buscar en preguntas y respuestas</label>
        <div class="search-field"><input class="text-input" type="search" id="faq-search" name="q"
          value="{html.escape(query, quote=True)}" placeholder="Por ejemplo: Excel, OCR o páginas" aria-describedby="faq-count" autocomplete="off">
          {help_link('search')}</div>
        <div class="search-actions">
          <div class="action-with-help"><button type="submit" class="secondary-button" data-help-action="search">Buscar</button>{help_link('search')}</div>
          <div class="action-with-help"><a class="text-action" href="/ayuda#faq" id="faq-clear" data-help-action="clear">Limpiar</a>{help_link('clear')}</div>
        </div>
      </form>
      <p id="faq-count" class="hint" role="status">{count} preguntas disponibles</p>
      <div id="faq-empty" class="faq-empty" {"hidden" if count else ""}>{mascot(96)}
        <h3>No encontramos esa respuesta</h3><p>Prueba otra palabra o consulta la guía de uso.</p></div>
      <div id="faq-list">{faq_html}</div>
    </section>
    <section id="guia" class="panel help-section" aria-labelledby="guide-title">
      <h2 id="guide-title">Tu primera conversión</h2><p class="hint">Del PDF a tus archivos editables en cuatro pasos.</p>
      <ol class="guide-steps">
        <li><strong>Prepara tu PDF</strong><p>Un archivo de hasta 25 MB y 100 páginas, sin contraseña. Comprueba que abre correctamente.</p></li>
        <li><strong>Elige lo que necesitas</strong><p>Excel para tablas, Word para texto y tablas, o TXT para texto sin formato. Puedes marcar varios. Las páginas son opcionales; activa OCR si es un escaneo.</p></li>
        <li><strong>Convierte y espera</strong><p>Presiona Convertir PDF una vez. Mantén la página abierta hasta ver los resultados.</p></li>
        <li><strong>Descarga y revisa</strong><p>Guarda tus archivos y compáralos con el original. Consulta las notas: la revisión es parte de toda conversión.</p></li>
      </ol>
      <div class="action-with-help"><a href="/" class="primary-button" data-help-action="new">Empezar una conversión</a>{help_link('new')}</div>
    </section>
    <section id="acciones" class="panel help-section" aria-labelledby="actions-title">
      <h2 id="actions-title">¿Qué hace cada acción?</h2><p class="hint">También puedes pulsar el botón ? junto a una acción, sin ejecutarla.</p>
      {action_help}
    </section>
  </div>
</div>"""
