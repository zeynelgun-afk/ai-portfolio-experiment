"""Extract readable public article bodies while keeping excerpts visibly distinct."""
from html.parser import HTMLParser
import ipaddress
import json
import re
import socket
from urllib.parse import urljoin, urlsplit

import requests

MAX_ARTICLES = 12
MAX_PAGE_BYTES = 1_500_000
MAX_BODY_CHARS = 18_000
MIN_BODY_CHARS = 1_200
MIN_BODY_PARAGRAPHS = 4
USER_AGENT = 'AI-Portfolio-Experiment/1.0 (+https://github.com/zeynelgun-afk/ai-portfolio-experiment)'


class _PageParser(HTMLParser):
    BLOCKED = {'script', 'style', 'noscript', 'svg', 'nav', 'header', 'footer', 'aside', 'form'}
    BLOCK_TAGS = {'p', 'br', 'div', 'section', 'article', 'main', 'li', 'h1', 'h2', 'h3', 'blockquote'}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.blocked = 0
        self.paragraphs = []
        self.current = []
        self.article_depth = 0
        self.content_scope_tags = []
        self.fallback_paragraphs = []
        self.fallback_current = []
        self.in_fallback_p = False
        self.in_json_ld = False
        self.json_ld = []
        self.json_blobs = []
        self.in_title = False
        self.title = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag in self.BLOCKED:
            self.blocked += 1
            if tag == 'script' and 'ld+json' in attrs.get('type', '').lower():
                self.in_json_ld = True
            return
        if self.blocked:
            return
        if tag == 'title':
            self.in_title = True
        content_scope = tag in {'article', 'main'} or (tag == 'div' and any(token in attrs.get('class', '').lower()
                for token in ('article-body', 'article-content', 'story-body', 'post-content', 'entry-content')))
        if content_scope:
            self.article_depth += 1
            self.content_scope_tags.append(tag)
        if tag == 'p':
            self.in_fallback_p = True
            self.fallback_current = []
            if self.article_depth:
                self.current = []

    def handle_endtag(self, tag):
        if tag in self.BLOCKED and self.blocked:
            self.blocked -= 1
            if tag == 'script' and self.in_json_ld:
                self.json_blobs.append(''.join(self.json_ld))
                self.json_ld = []
                self.in_json_ld = False
            return
        if self.blocked:
            return
        if tag == 'title':
            self.in_title = False
        if tag == 'p' and self.in_fallback_p:
            text = ' '.join(''.join(self.fallback_current).split())
            if text:
                self.fallback_paragraphs.append(text)
            if self.article_depth and text:
                self.paragraphs.append(text)
            self.in_fallback_p = False
        if tag in self.content_scope_tags:
            self.content_scope_tags.remove(tag)
            self.article_depth = max(0, self.article_depth - 1)

    def handle_data(self, data):
        if self.in_json_ld:
            self.json_ld.append(data)
            return
        if self.in_title:
            self.title.append(data)
        if self.blocked:
            return
        if self.in_fallback_p:
            self.fallback_current.append(data)

    def _article_body(self, value):
        if isinstance(value, dict):
            body = value.get('articleBody')
            if isinstance(body, str) and len(body.strip()) > 200:
                return body
            graph = value.get('@graph')
            if isinstance(graph, list):
                for item in graph:
                    found = self._article_body(item)
                    if found:
                        return found
        elif isinstance(value, list):
            for item in value:
                found = self._article_body(item)
                if found:
                    return found
        return None

    def result(self):
        for raw in self.json_blobs:
            try:
                body = self._article_body(json.loads(raw))
            except (ValueError, TypeError):
                body = None
            if body:
                clean = ' '.join(body.split())[:MAX_BODY_CHARS]
                paragraph_count = len([p for p in re.split(r'\n\s*\n', body) if len(p.strip()) > 50])
                return clean, paragraph_count, 'json_ld_article_body', ''.join(self.title).strip()
        paragraphs = self.paragraphs if self.paragraphs else self.fallback_paragraphs
        body = '\n\n'.join(p for p in paragraphs if len(p) > 50)
        method = 'article_or_main_paragraphs' if self.paragraphs else 'page_paragraphs'
        return body[:MAX_BODY_CHARS], len([p for p in paragraphs if len(p) > 50]), method, ''.join(self.title).strip()


def _public_http_url(url):
    parts = urlsplit(url)
    if parts.scheme.lower() != 'https' or not parts.hostname or parts.username or parts.password:
        return False
    try:
        addresses = {item[4][0] for item in socket.getaddrinfo(parts.hostname, parts.port or 443,
                     type=socket.SOCK_STREAM)}
        return bool(addresses) and all(ipaddress.ip_address(address).is_global for address in addresses)
    except (OSError, ValueError):
        return False


def fetch_article(url):
    """Fetch a bounded HTTPS page; follow only public HTTPS redirects."""
    current = url
    for _ in range(4):
        if not _public_http_url(current):
            return None
        try:
            with requests.get(current, headers={'User-Agent': USER_AGENT,
                    'Accept': 'text/html,application/xhtml+xml'}, timeout=(4, 10),
                    allow_redirects=False, stream=True) as response:
                if response.is_redirect:
                    location = response.headers.get('Location')
                    if not location:
                        return None
                    current = urljoin(current, location)
                    continue
                response.raise_for_status()
                if 'html' not in response.headers.get('Content-Type', '').lower():
                    return None
                chunks, total = [], 0
                for chunk in response.iter_content(65536):
                    if not chunk:
                        continue
                    total += len(chunk)
                    if total > MAX_PAGE_BYTES:
                        break
                    chunks.append(chunk)
                content = b''.join(chunks)
                encoding = response.encoding or 'utf-8'
                return content.decode(encoding, errors='replace')
        except requests.RequestException:
            return None
    return None


def extract_article(html):
    parser = _PageParser()
    try:
        parser.feed(html)
        return parser.result()
    except Exception:
        return '', 0, 'parse_failed', ''


def enrich_news(news, fetcher=fetch_article, max_articles=MAX_ARTICLES):
    """Attach transient article bodies for analysis and durable coverage metadata."""
    output = []
    for index, row in enumerate(news):
        item = dict(row)
        item['content_read_status'] = 'provider_excerpt_only'
        item['body_word_count'] = 0
        item['body_extraction_method'] = None
        if index < max_articles:
            html = fetcher(item.get('url', ''))
            if html:
                body, paragraphs, method, page_title = extract_article(html)
                item['body_word_count'] = len(body.split())
                item['body_extraction_method'] = method
                if body and len(body) >= MIN_BODY_CHARS and paragraphs >= MIN_BODY_PARAGRAPHS:
                    item['content_read_status'] = 'article_body_extracted'
                    item['article_body_text'] = body
                    if page_title and not item.get('title'):
                        item['page_title'] = page_title[:300]
                else:
                    item['content_read_status'] = 'body_unavailable_or_too_short_excerpt_only'
        output.append(item)
    return output


def strip_transient_bodies(news):
    return [{key: value for key, value in row.items() if key != 'article_body_text'} for row in news]
