#!/usr/bin/env python3
# VOD/movie WordPress draft pipeline.
# It collects factual movie data, builds six original article drafts per title,
# creates simple safe featured images, and can upload drafts to WordPress.
# Use it for draft generation first; keep final publishing as a manual decision.

from __future__ import annotations

import argparse
import base64
import dataclasses
import html.parser
import json
import os
import pathlib
import re
import sys
import textwrap
import unicodedata
from datetime import datetime
from typing import Iterable
from urllib.parse import urljoin

import requests

try:
    from PIL import Image, ImageDraw, ImageFont
except Exception:  # pragma: no cover - Pillow is optional for metadata-only runs.
    Image = None
    ImageDraw = None
    ImageFont = None


REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT_ROOT = REPO_ROOT / "outputs" / "vod-wordpress"
HTTP_TIMEOUT_SEC = 30
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (compatible; team-info-vod-wordpress/1.0; "
    "+https://example.invalid/local-tool)"
)


@dataclasses.dataclass
class MovieFact:
    title: str
    source_url: str
    release_label: str = ""
    summary: str = ""
    director: str = ""
    cast: str = ""
    service: str = ""


@dataclasses.dataclass(frozen=True)
class ArticleTemplate:
    key: str
    title_format: str
    image_label: str
    spoiler: bool
    category: str
    tags: tuple[str, ...]
    intent: str
    headings: tuple[str, ...]


ARTICLE_TEMPLATES: tuple[ArticleTemplate, ...] = (
    ArticleTemplate(
        key="review",
        title_format="映画『{title}』レビュー｜極限ゲームと生き残りの選択、観るべき作品か？",
        image_label="レビュー",
        spoiler=False,
        category="映画レビュー",
        tags=("レビュー", "面白い", "つまらない", "ネタバレなし"),
        intent="公開直後に「面白い？」「どんな映画？」で検索する読者向け。",
        headings=(
            "映画『{title}』はどんな作品？",
            "ネタバレなしの見どころ",
            "面白いと感じやすいポイント",
            "つまらないと感じる可能性がある点",
            "どんな人におすすめか",
        ),
    ),
    ArticleTemplate(
        key="cast",
        title_format="映画『{title}』キャスト・登場人物・設定まとめ｜参加者・運営側・黒幕の役割を整理",
        image_label="キャスト",
        spoiler=False,
        category="キャスト",
        tags=("キャスト", "登場人物", "相関図", "黒幕"),
        intent="「誰が誰？」「どんな役割？」を調べる読者向け。",
        headings=(
            "『{title}』の主要キャスト一覧",
            "参加者側の立場と役割",
            "運営側・黒幕側の見方",
            "人物関係を理解するポイント",
            "鑑賞前に押さえたい設定",
        ),
    ),
    ArticleTemplate(
        key="ending",
        title_format="映画『{title}』ラスト結末・伏線考察｜勝利の意味、選択の理由、残された謎を解説",
        image_label="結末考察",
        spoiler=True,
        category="考察",
        tags=("ネタバレ", "結末", "ラスト", "伏線", "考察"),
        intent="視聴後にラストの意味や伏線を調べる読者向け。",
        headings=(
            "ここからネタバレあり",
            "ラストで何が起きたのか",
            "勝利の意味と選択の理由",
            "回収された伏線",
            "残された謎と続編の可能性",
        ),
    ),
    ArticleTemplate(
        key="original",
        title_format="映画『{title}』原作・元ネタとの違い比較｜変更点、削除要素、テーマの違いを解説",
        image_label="原作比較",
        spoiler=True,
        category="原作比較",
        tags=("原作", "元ネタ", "リメイク", "違い"),
        intent="原作、リメイク、過去作との違いを調べる読者向け。",
        headings=(
            "『{title}』に原作や元ネタはある？",
            "映画版で変わった可能性がある点",
            "削除・追加された要素の見方",
            "テーマがどう深まったか",
            "原作を読む・過去作を見る価値",
        ),
    ),
    ArticleTemplate(
        key="streaming",
        title_format="映画『{title}』配信はいつ？Netflix・Amazon Prime Video・U-NEXT・Hulu最新情報まとめ",
        image_label="配信情報",
        spoiler=False,
        category="配信情報",
        tags=("配信", "どこで見れる", "Netflix", "U-NEXT", "Hulu"),
        intent="公開後から長期で「どこで見れる？」を調べる読者向け。",
        headings=(
            "『{title}』はどこで見れる？",
            "配信開始日の最新情報",
            "Netflix・Amazon Prime Video・U-NEXT・Huluの状況",
            "レンタル配信・購入配信の可能性",
            "配信情報を確認するときの注意点",
        ),
    ),
    ArticleTemplate(
        key="disc",
        title_format="映画『{title}』Blu-ray・DVD発売日はいつ？特典・限定版・予約情報まとめ",
        image_label="Blu-ray/DVD",
        spoiler=False,
        category="Blu-ray/DVD",
        tags=("Blu-ray", "DVD", "発売日", "特典", "予約"),
        intent="予約、発売日、特典、中古需要まで拾う収益記事向け。",
        headings=(
            "『{title}』Blu-ray・DVD発売日はいつ？",
            "予約開始時期の目安",
            "特典・限定版で確認したいポイント",
            "メイキングや未公開シーンは収録される？",
            "配信と円盤、どちらを選ぶべきか",
        ),
    ),
)


class ComingPageParser(html.parser.HTMLParser):
    def __init__(self, base_url: str) -> None:
        super().__init__(convert_charrefs=True)
        self.base_url = base_url
        self.current_tag = ""
        self.current_href = ""
        self.current_release = ""
        self.movies: list[MovieFact] = []
        self._active_movie: MovieFact | None = None
        self._text_buffer: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = {k: v or "" for k, v in attrs}
        if tag in {"h2", "h3", "li", "p"}:
            self.current_tag = tag
            self._text_buffer = []
        if tag == "a":
            self.current_href = attrs_dict.get("href", "")

    def handle_data(self, data: str) -> None:
        text = normalize_space(data)
        if text:
            self._text_buffer.append(text)

    def handle_endtag(self, tag: str) -> None:
        if tag not in {"h2", "h3", "li", "p"}:
            if tag == "a":
                self.current_href = ""
            return

        text = normalize_space(" ".join(self._text_buffer))
        if tag == "h2" and "公開" in text:
            self.current_release = text
        elif tag == "h3" and text and self.current_href:
            href = urljoin(self.base_url, self.current_href)
            if "/movie/" in href:
                movie = MovieFact(title=text, source_url=href, release_label=self.current_release)
                self.movies.append(movie)
                self._active_movie = movie
        elif self._active_movie and text:
            assign_movie_detail(self._active_movie, text)

        self.current_tag = ""
        self._text_buffer = []
        if tag == "a":
            self.current_href = ""


def normalize_space(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def assign_movie_detail(movie: MovieFact, text: str) -> None:
    if not movie.summary and len(text) >= 35 and "映画館を探す" not in text:
        movie.summary = text
    if "監督" in text and not movie.director:
        movie.director = text
    elif not movie.cast and "," in text and len(text) >= 8:
        movie.cast = text
    if not movie.service:
        match = re.search(r"(Netflix|Amazon|Prime Video|Disney\+|U-NEXT|Hulu|Lemino|ABEMA|FOD|WOWOW)", text, re.I)
        if match:
            movie.service = match.group(1)


def fetch_coming_page(url: str) -> list[MovieFact]:
    response = requests.get(
        url,
        headers={"User-Agent": DEFAULT_USER_AGENT},
        timeout=HTTP_TIMEOUT_SEC,
    )
    response.raise_for_status()
    parser = ComingPageParser(url)
    parser.feed(response.text)
    return dedupe_movies(parser.movies)


def dedupe_movies(movies: Iterable[MovieFact]) -> list[MovieFact]:
    seen: set[str] = set()
    result: list[MovieFact] = []
    for movie in movies:
        key = movie.source_url or movie.title
        if key in seen:
            continue
        seen.add(key)
        result.append(movie)
    return result


def slugify(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value).lower()
    ascii_part = "".join(ch for ch in normalized if ch.isascii() and ch.isalnum())
    if ascii_part:
        return ascii_part[:80]
    encoded = base64.urlsafe_b64encode(value.encode("utf-8")).decode("ascii").rstrip("=")
    return encoded[:80].lower()


def build_article(movie: MovieFact, template: ArticleTemplate) -> dict:
    title = template.title_format.format(title=movie.title)
    headings = [heading.format(title=movie.title) for heading in template.headings]
    body = build_body(movie, template, headings)
    return {
        "key": template.key,
        "title": title,
        "slug": f"{slugify(movie.title)}-{template.key}",
        "status": "draft",
        "category": template.category,
        "tags": list(dict.fromkeys((movie.title, *template.tags))),
        "spoiler": template.spoiler,
        "search_intent": template.intent,
        "body_markdown": body,
        "featured_image": None,
        "featured_image_prompt": build_image_prompt(movie, template),
    }


def build_body(movie: MovieFact, template: ArticleTemplate, headings: list[str]) -> str:
    spoiler_note = (
        "この記事はネタバレを含みます。未視聴の方は、結末や重要な展開に触れる部分に注意してください。"
        if template.spoiler
        else "この記事はネタバレなしで、鑑賞前に知りたい情報を中心に整理します。"
    )
    facts = [
        f"- 作品名: {movie.title}",
        f"- 公開・配信時期: {movie.release_label or '未確認'}",
        f"- 配信サービス: {movie.service or '未確認'}",
        f"- 監督: {movie.director or '未確認'}",
        f"- キャスト: {movie.cast or '未確認'}",
        f"- 参照元: {movie.source_url}",
    ]
    intro = (
        f"映画『{movie.title}』について、検索されやすい疑問を整理します。"
        f"{spoiler_note} 情報は公式発表や参照元の事実情報をもとに更新し、"
        "本文は転載ではなく独自の観点でまとめます。"
    )
    sections = []
    for index, heading in enumerate(headings, start=1):
        sections.append(f"## {heading}\n\n{build_section_text(movie, template, index)}")
    closing = (
        f"『{movie.title}』は、公開直後の評判だけでなく、配信開始・円盤発売・原作比較などで"
        "継続的に検索される余地があります。最新情報が発表された場合は、配信サービス名、発売日、"
        "特典内容を確認して追記してください。"
    )
    return "\n\n".join([intro, "## 基本情報\n\n" + "\n".join(facts), *sections, "## まとめ\n\n" + closing])


def build_section_text(movie: MovieFact, template: ArticleTemplate, index: int) -> str:
    base = {
        "review": [
            "まず押さえたいのは、作品の入口になる設定です。鑑賞前の読者は、細かい展開よりも「どんな緊張感の映画なのか」「自分に合う作品なのか」を知りたがっています。",
            "見どころは、登場人物が追い込まれる状況と、その中で何を選ぶかにあります。過度に結末を説明せず、映像のテンポ、サスペンス性、感情移入のしやすさを中心に整理します。",
            "面白いと感じやすいのは、ルールのあるサバイバル、心理戦、社会風刺が好きな人です。単なるアクションではなく、選択の重さを楽しめるかが評価の分かれ目です。",
            "一方で、説明不足に感じる場面や、重いテーマが苦手な人には合わない可能性があります。期待値を調整することで、鑑賞後の満足度を判断しやすくなります。",
            "おすすめできるのは、デスゲーム系、逃走劇、近未来サスペンスが好きな人です。迷っている読者には、キャストや原作情報も合わせて確認する導線を置きます。",
        ],
        "cast": [
            "キャスト記事では、名前の羅列ではなく、物語上の立場で整理することが重要です。参加者、運営側、外部の協力者、黒幕候補に分けると読者が理解しやすくなります。",
            "参加者側は、ゲームに巻き込まれる理由、勝ち残る動機、他者との関係性を中心にまとめます。役名が未発表の場合は、俳優名と確認済み情報だけを掲載します。",
            "運営側や黒幕側は、作品の緊張感を作る存在です。ネタバレなしの記事では断定を避け、公式に明かされている範囲で役割を整理します。",
            "相関図を入れる場合は、敵味方を固定しすぎず、公開前は「関係が変化する可能性がある」前提で作ると更新しやすくなります。",
            "鑑賞前に人物関係を把握しておくと、物語の駆け引きが追いやすくなります。公開後は判明した役割を追記し、ネタバレ記事へ内部リンクします。",
        ],
        "ending": [
            "結末考察では、まずラストで起きた出来事を時系列で整理します。読者は感想より先に「結局どういう意味だったのか」を確認したいからです。",
            "勝利の意味は、ゲーム上の勝敗だけでなく、主人公が何を守ったのか、何を失ったのかで変わります。選択の理由を人物の動機から読み解きます。",
            "伏線は、序盤の台詞、ルール説明、運営側の違和感、映像上の反復などに分けて整理します。未回収に見える要素も、続編や原作との関係で解釈できます。",
            "残された謎は、断定しすぎず複数の見方を提示します。「意味不明」と検索する読者には、考えられる解釈を並べる構成が有効です。",
            "最後に、続編の可能性やシリーズ展開の余地を整理します。公式発表がない場合は、未発表であることを明記します。",
        ],
        "original": [
            "原作比較では、まず原作や過去映像化作品の有無を整理します。タイトルが同じでも、設定やテーマが大きく変わる場合があります。",
            "変更点は、人物設定、時代背景、ゲームのルール、結末の扱いに分けると読みやすくなります。未確認情報は推測として扱わず、更新予定として残します。",
            "削除された要素がある場合、それは尺の都合だけでなく、現代の観客向けにテーマを絞った可能性があります。何が省かれたかより、なぜ省かれたかを考えます。",
            "テーマの違いは、原作が描いた社会批評と映画版が強調する感情線を比べると見えやすくなります。",
            "原作を読む価値は、映画では描き切れない背景や心理描写を補える点にあります。鑑賞後の読者に向けて、読む順番や見る順番を提案します。",
        ],
        "streaming": [
            "配信情報記事では、まず現在確認できるサービス名と開始日を明記します。未発表の場合は、未定と書き、推測でサービス名を断定しません。",
            "配信開始日は、劇場公開日、先行配信、レンタル配信、見放題配信で異なります。読者が知りたいのは「今日見れるか」なので、状況別に整理します。",
            "Netflix、Amazon Prime Video、U-NEXT、Huluなど主要サービスごとに確認欄を作ると、更新時に差し替えやすくなります。",
            "レンタルや購入配信は、見放題より早く始まることがあります。料金、字幕・吹替、画質の違いも収益導線にできます。",
            "最新情報は変わりやすいため、記事上部に更新日を入れます。古い情報で読者を誘導しないことが長期運用では重要です。",
        ],
        "disc": [
            "Blu-ray・DVD記事では、発売日が未発表でも予約開始時期の目安を説明できます。ただし日付は公式発表が出るまで断定しません。",
            "予約開始は、劇場公開後や配信開始後に発表されることが多いため、読者には確認ポイントを示します。",
            "特典は、初回限定版、店舗別特典、メイキング、ブックレット、未公開シーンなどに分けると比較しやすくなります。",
            "メイキングや未公開シーンは、作品の裏側を知りたいファンに刺さる要素です。発表後に内容を追記できる見出しを先に用意しておきます。",
            "配信と円盤のどちらが良いかは、すぐ見たい人、手元に残したい人、特典が欲しい人で判断が変わります。購入導線は押しつけず、比較で自然に置きます。",
        ],
    }
    paragraphs = base[template.key]
    detail = paragraphs[min(index - 1, len(paragraphs) - 1)]
    summary = f"参照元で確認できた概要: {movie.summary}" if movie.summary else "参照元の詳細情報は取得後に追記します。"
    return f"{detail}\n\n{summary}"


def build_image_prompt(movie: MovieFact, template: ArticleTemplate) -> str:
    return (
        f"1200x630 OGP featured image for a Japanese movie blog article. "
        f"Theme: {template.image_label}. Title text: {movie.title}. "
        "Original cinematic design, no official poster, no real actor likeness, no trademarked logo. "
        "High contrast, readable Japanese headline area, modern editorial layout."
    )


def create_featured_image(path: pathlib.Path, movie: MovieFact, template: ArticleTemplate) -> None:
    if Image is None or ImageDraw is None:
        raise RuntimeError("Pillow is not installed; cannot create featured images.")
    width, height = 1200, 630
    palettes = {
        "review": ((30, 34, 44), (220, 64, 52)),
        "cast": ((24, 44, 54), (48, 153, 117)),
        "ending": ((18, 20, 28), (128, 83, 177)),
        "original": ((42, 35, 28), (215, 168, 81)),
        "streaming": ((20, 38, 59), (66, 153, 225)),
        "disc": ((35, 35, 42), (196, 196, 206)),
    }
    bg, accent = palettes.get(template.key, ((28, 32, 40), (230, 80, 60)))
    image = Image.new("RGB", (width, height), bg)
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, width, 18), fill=accent)
    draw.rectangle((64, 86, 180, 96), fill=accent)
    draw.ellipse((820, -180, 1280, 280), outline=accent, width=18)
    draw.ellipse((910, 300, 1120, 510), outline=(255, 255, 255), width=6)
    draw.rectangle((64, 448, 1136, 450), fill=accent)

    font_large = load_font(62)
    font_mid = load_font(42)
    font_small = load_font(28)
    title_lines = wrap_text_for_image(movie.title, 13, max_lines=2)
    y = 145
    for line in title_lines:
        draw.text((64, y), line, fill=(255, 255, 255), font=font_large)
        y += 76
    draw.text((66, 350), template.image_label, fill=accent, font=font_mid)
    draw.text((66, 520), "VOD MOVIE GUIDE", fill=(235, 235, 235), font=font_small)
    draw.text((760, 520), "original draft image", fill=(210, 210, 210), font=font_small)
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path, format="PNG")


def load_font(size: int):
    if ImageFont is None:
        return None
    candidates = [
        pathlib.Path(os.environ.get("WINDIR", "C:\\Windows")) / "Fonts" / "meiryo.ttc",
        pathlib.Path(os.environ.get("WINDIR", "C:\\Windows")) / "Fonts" / "YuGothB.ttc",
        pathlib.Path("/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc"),
        pathlib.Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return ImageFont.truetype(str(candidate), size=size)
    return ImageFont.load_default()


def wrap_text_for_image(text: str, width: int, max_lines: int) -> list[str]:
    lines: list[str] = []
    current = ""
    for ch in text:
        if len(current) >= width:
            lines.append(current)
            current = ch
        else:
            current += ch
        if len(lines) >= max_lines:
            break
    if current and len(lines) < max_lines:
        lines.append(current)
    return lines or [text[:width]]


def write_movie_bundle(movie: MovieFact, output_dir: pathlib.Path, create_images: bool) -> dict:
    movie_dir = output_dir / slugify(movie.title)
    articles_dir = movie_dir / "articles"
    images_dir = movie_dir / "images"
    articles_dir.mkdir(parents=True, exist_ok=True)
    bundle = {
        "movie": dataclasses.asdict(movie),
        "articles": [],
    }
    for template in ARTICLE_TEMPLATES:
        article = build_article(movie, template)
        image_path = images_dir / f"{article['slug']}.png"
        if create_images:
            create_featured_image(image_path, movie, template)
            article["featured_image"] = str(image_path)
        article_path = articles_dir / f"{article['slug']}.md"
        article_path.write_text(article_to_markdown(article), encoding="utf-8")
        article["draft_path"] = str(article_path)
        bundle["articles"].append(article)
    manifest_path = movie_dir / "manifest.json"
    manifest_path.write_text(json.dumps(bundle, ensure_ascii=False, indent=2), encoding="utf-8")
    return bundle


def article_to_markdown(article: dict) -> str:
    frontmatter = {
        "title": article["title"],
        "slug": article["slug"],
        "status": article["status"],
        "category": article["category"],
        "tags": article["tags"],
        "spoiler": article["spoiler"],
        "featured_image": article["featured_image"],
        "featured_image_prompt": article["featured_image_prompt"],
    }
    return "---\n" + json.dumps(frontmatter, ensure_ascii=False, indent=2) + "\n---\n\n" + article["body_markdown"] + "\n"


def wp_headers(username: str, app_password: str) -> dict[str, str]:
    token = base64.b64encode(f"{username}:{app_password}".encode("utf-8")).decode("ascii")
    return {"Authorization": f"Basic {token}", "User-Agent": DEFAULT_USER_AGENT}


def upload_media(base_url: str, headers: dict[str, str], image_path: pathlib.Path, title: str) -> int:
    endpoint = base_url.rstrip("/") + "/wp-json/wp/v2/media"
    data = image_path.read_bytes()
    media_headers = {
        **headers,
        "Content-Disposition": f'attachment; filename="{image_path.name}"',
        "Content-Type": "image/png",
    }
    response = requests.post(endpoint, headers=media_headers, data=data, timeout=HTTP_TIMEOUT_SEC)
    response.raise_for_status()
    media = response.json()
    media_id = int(media["id"])
    requests.post(
        f"{endpoint}/{media_id}",
        headers={**headers, "Content-Type": "application/json"},
        json={"title": title, "alt_text": title},
        timeout=HTTP_TIMEOUT_SEC,
    ).raise_for_status()
    return media_id


def create_wp_post(base_url: str, headers: dict[str, str], article: dict, featured_media: int | None, status: str) -> int:
    endpoint = base_url.rstrip("/") + "/wp-json/wp/v2/posts"
    payload = {
        "title": article["title"],
        "slug": article["slug"],
        "status": status,
        "content": markdown_to_wp_content(article["body_markdown"]),
        "excerpt": article["search_intent"],
    }
    if featured_media:
        payload["featured_media"] = featured_media
    response = requests.post(
        endpoint,
        headers={**headers, "Content-Type": "application/json"},
        json=payload,
        timeout=HTTP_TIMEOUT_SEC,
    )
    response.raise_for_status()
    return int(response.json()["id"])


def markdown_to_wp_content(markdown: str) -> str:
    lines = []
    for raw_line in markdown.splitlines():
        line = raw_line.rstrip()
        if line.startswith("## "):
            lines.append(f"<h2>{escape_html(line[3:])}</h2>")
        elif line.startswith("- "):
            lines.append(f"<p>{escape_html(line)}</p>")
        elif line:
            lines.append(f"<p>{escape_html(line)}</p>")
    return "\n".join(lines)


def escape_html(value: str) -> str:
    return (
        value.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def upload_bundle_to_wordpress(bundle: dict, status: str) -> list[dict]:
    base_url = require_env("WP_BASE_URL")
    username = require_env("WP_USERNAME")
    app_password = require_env("WP_APP_PASSWORD")
    headers = wp_headers(username, app_password)
    results = []
    for article in bundle["articles"]:
        media_id = None
        if article.get("featured_image"):
            media_id = upload_media(base_url, headers, pathlib.Path(article["featured_image"]), article["title"])
        post_id = create_wp_post(base_url, headers, article, media_id, status)
        results.append({"slug": article["slug"], "post_id": post_id, "media_id": media_id})
    return results


def require_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def load_movies_from_json(path: pathlib.Path) -> list[MovieFact]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    items = payload if isinstance(payload, list) else payload.get("movies", [])
    return [MovieFact(**item) for item in items]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create VOD movie WordPress draft bundles.")
    parser.add_argument("--coming-url", help="eiga.com coming page URL, e.g. https://eiga.com/coming/202608/")
    parser.add_argument("--input-json", type=pathlib.Path, help="Local movie facts JSON for offline/manual runs.")
    parser.add_argument("--movie-title", help="Only process a title containing this text.")
    parser.add_argument("--limit", type=int, default=1, help="Maximum movies to process. Default: 1.")
    parser.add_argument("--output-dir", type=pathlib.Path, help="Output directory. Default: outputs/vod-wordpress/<timestamp>.")
    parser.add_argument("--no-images", action="store_true", help="Skip local featured image creation.")
    parser.add_argument("--wordpress-draft", action="store_true", help="Upload generated drafts and featured images to WordPress.")
    parser.add_argument("--wp-status", default="draft", choices=("draft", "pending", "private"), help="WordPress post status.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.coming_url and not args.input_json:
        print("[ERROR] --coming-url or --input-json is required.", file=sys.stderr)
        return 2

    movies = load_movies_from_json(args.input_json) if args.input_json else fetch_coming_page(args.coming_url)
    if args.movie_title:
        movies = [movie for movie in movies if args.movie_title in movie.title]
    movies = movies[: max(args.limit, 0)]
    if not movies:
        print("[ERROR] No movies matched.", file=sys.stderr)
        return 1

    output_dir = args.output_dir or DEFAULT_OUTPUT_ROOT / datetime.now().strftime("%Y%m%d-%H%M%S")
    output_dir.mkdir(parents=True, exist_ok=True)
    run_manifest = {"source": args.coming_url or str(args.input_json), "movies": []}

    for movie in movies:
        bundle = write_movie_bundle(movie, output_dir, create_images=not args.no_images)
        if args.wordpress_draft:
            bundle["wordpress"] = upload_bundle_to_wordpress(bundle, args.wp_status)
        run_manifest["movies"].append(bundle)

    manifest_path = output_dir / "run_manifest.json"
    manifest_path.write_text(json.dumps(run_manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(textwrap.dedent(f"""
    Done.
    Output: {output_dir}
    Manifest: {manifest_path}
    Movies: {len(movies)}
    Articles: {len(movies) * len(ARTICLE_TEMPLATES)}
    """).strip())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
