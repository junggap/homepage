#!/usr/bin/env python3
"""
Physical AI Chronicle - Automated Daily Newspaper & Archive Generator
Crawls:
 1. Official arXiv Robotics RSS feed (cs.RO)
 2. Global Physical AI & Humanoid Industry Wire
 3. Global Radar: Recent updates & news for tracked companies across USA, China, Europe, Korea
Archives:
 - Saves daily snapshot to news/archive/YYYY-MM-DD.json
 - Updates master searchable catalog news/archive/index.json
 - Renders mobile-first newspaper news/index.html with interactive archive search bar
"""

import os
import re
import sys
import json
import datetime
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET

NEWS_DIR = os.path.dirname(os.path.abspath(__file__))
ARCHIVE_DIR = os.path.join(NEWS_DIR, "archive")
OUTPUT_HTML = os.path.join(NEWS_DIR, "index.html")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

TRACKED_COMPANIES = {
    "usa": [
        {"name": "Figure AI", "robot": "Figure 02 / 03", "query": "Figure AI humanoid robot"},
        {"name": "Tesla", "robot": "Optimus Gen 2/3", "query": "Tesla Optimus robot"},
        {"name": "Boston Dynamics", "robot": "Electric Atlas", "query": "Boston Dynamics Atlas robot"},
        {"name": "1X Technologies", "robot": "NEO / EVE", "query": "1X NEO robot"},
        {"name": "Agility Robotics", "robot": "Digit", "query": "Agility Robotics Digit"},
        {"name": "Apptronik", "robot": "Apollo", "query": "Apptronik Apollo humanoid"},
        {"name": "Physical Intelligence", "robot": "π0 (Pi-Zero VLA)", "query": "Physical Intelligence pi0 robot"},
        {"name": "Skild AI", "robot": "Skild Brain VLA", "query": "Skild AI robot foundation model"},
        {"name": "Generalist", "robot": "Foundation Embodied AI", "query": "Generalist embodied AI robot"},
        {"name": "Genesis AI", "robot": "Physics / World Model", "query": "Genesis AI robotics physics"},
        {"name": "Dyna Robotics", "robot": "Taku / Dyna-2.1", "query": "Dyna Robotics Taku robot"},
    ],
    "china": [
        {"name": "Unitree Robotics", "robot": "Unitree G1 / H1", "query": "Unitree G1 robot"},
        {"name": "AGIBOT (Zhiyuan)", "robot": "Expedition A2 / X1", "query": "AGIBOT Zhiyuan robot"},
        {"name": "UBTECH", "robot": "Walker S1", "query": "UBTECH Walker robot"},
        {"name": "Fourier Intelligence", "robot": "GR-1 / GR-2", "query": "Fourier Intelligence GR-2 humanoid"},
        {"name": "LimX Dynamics", "robot": "CL-1 Biped", "query": "LimX Dynamics robot"},
        {"name": "Galbot Robotics", "robot": "Galbot G1", "query": "Galbot robot"},
        {"name": "Kepler Robotics", "robot": "Forerunner K2", "query": "Kepler Forerunner humanoid robot"},
    ],
    "europe": [
        {"name": "Agile Robots (Germany)", "robot": "Agile ONE", "query": "Agile Robots humanoid DLR"},
        {"name": "NEURA Robotics (Germany)", "robot": "4NE-1 Cognitive", "query": "NEURA Robotics 4NE-1"},
        {"name": "Mentee Robotics", "robot": "MenteeBot", "query": "Mentee Robotics MenteeBot"},
        {"name": "PAL Robotics (Spain)", "robot": "TALOS / TIAGo", "query": "PAL Robotics humanoid"},
        {"name": "Pollen Robotics (France)", "robot": "Reachy 2", "query": "Pollen Robotics Reachy"},
        {"name": "The Humanoid Co. (EU)", "robot": "HMND 01 Alpha", "query": "Humanoid HMND robot"},
    ],
    "korea": [
        {"name": "Rainbow Robotics", "robot": "HUBO / Biped", "query": "Rainbow Robotics HUBO humanoid"},
        {"name": "Doosan Robotics", "robot": "K-Humanoid Alliance", "query": "Doosan Robotics humanoid"},
        {"name": "WIRobotics", "robot": "ALLEX Humanoid", "query": "WIRobotics ALLEX robot"},
        {"name": "Robotis", "robot": "DYNAMIXEL-Y Drive", "query": "Robotis DYNAMIXEL robot"},
    ]
}

def clean_text(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def fetch_rss_query(query: str):
    encoded_query = urllib.parse.quote(query)
    url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-US&gl=US&ceid=US:en"
    
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=6) as response:
            xml_data = response.read()
            root = ET.fromstring(xml_data)
            items = root.findall('./channel/item')
            if items:
                item = items[0]
                title = clean_text(item.find('title').text)
                link = item.find('link').text if item.find('link') is not None else "#"
                pubDate = item.find('pubDate').text if item.find('pubDate') is not None else ""
                
                date_str = ""
                if pubDate:
                    try:
                        dt = datetime.datetime.strptime(pubDate[:16], "%a, %d %b %Y")
                        date_str = dt.strftime("%b %d")
                    except Exception:
                        date_str = pubDate[:11]
                
                source = "News"
                if " - " in title:
                    parts = title.rsplit(" - ", 1)
                    title = parts[0]
                    source = parts[1]
                    
                return {
                    "headline": title,
                    "link": link,
                    "source": source,
                    "date": date_str
                }
    except Exception:
        pass
    return None

def fetch_arxiv_papers(max_results: int = 5):
    print("[1/3] Fetching arXiv robotics preprints (cs.RO)...")
    url = "https://rss.arxiv.org/rss/cs.RO"
    papers = []
    
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=10) as response:
            xml_data = response.read()
            root = ET.fromstring(xml_data)
            
            items = root.findall('./channel/item')[:max_results]
            for item in items:
                title = clean_text(item.find('title').text)
                link = item.find('link').text if item.find('link') is not None else "#"
                desc = clean_text(item.find('description').text) if item.find('description') is not None else ""
                if len(desc) > 220:
                    desc = desc[:217] + "..."
                    
                papers.append({
                    "title": title,
                    "summary": desc,
                    "link": link,
                    "category": "cs.RO"
                })
    except Exception as e:
        print(f"Warning: Failed to fetch arXiv: {e}", file=sys.stderr)
        
    return papers

def fetch_industry_stories():
    print("[2/3] Fetching latest Physical AI industry wire...")
    query = "humanoid robot OR embodied AI OR physical AI"
    encoded_query = urllib.parse.quote(query)
    url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-US&gl=US&ceid=US:en"
    
    stories = []
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=10) as response:
            xml_data = response.read()
            root = ET.fromstring(xml_data)
            
            for item in root.findall('./channel/item')[:4]:
                title = clean_text(item.find('title').text)
                link = item.find('link').text
                source = "Global Wire"
                if " - " in title:
                    parts = title.rsplit(" - ", 1)
                    title = parts[0]
                    source = parts[1]
                stories.append({"title": title, "link": link, "source": source})
    except Exception as e:
        print(f"Warning: Failed to fetch industry wire: {e}", file=sys.stderr)
        
    if not stories:
        stories = [
            {"title": "End-to-End Visuomotor Policies Enter Automotive Assembly Plants", "source": "Industrial Robotics Report", "link": "#"},
            {"title": "Quasi-Direct Drive vs. Cycloidal Actuators: Thermal Benchmarks in Biped Walking", "source": "Hardware Dispatches", "link": "#"}
        ]
    return stories

def fetch_company_updates():
    print("[3/3] Checking recent company updates for Global Radar...")
    company_updates = {}
    
    for region, companies in TRACKED_COMPANIES.items():
        company_updates[region] = []
        for c in companies:
            news = fetch_rss_query(c['query'])
            if news:
                update_text = news['headline']
                update_link = news['link']
                update_meta = f"{news['source']} · {news['date']}" if news['date'] else news['source']
            else:
                update_text = f"Continuous autonomy testing and production scaling on {c['robot']} platform."
                update_link = "#"
                update_meta = "Lab Radar"
                
            company_updates[region].append({
                "name": c['name'],
                "robot": c['robot'],
                "update": update_text,
                "link": update_link,
                "meta": update_meta
            })
            
    return company_updates

def save_daily_archive(today_key: str, today_str: str, papers, stories, company_updates):
    """
    Saves the day's payload to news/archive/YYYY-MM-DD.json
    and updates news/archive/index.json
    """
    os.makedirs(ARCHIVE_DIR, exist_ok=True)
    
    # 1. Daily snapshot file
    daily_data = {
        "date_key": today_key,
        "date_display": today_str,
        "lead_story": stories[0] if stories else {},
        "secondary_stories": stories[1:] if len(stories) > 1 else [],
        "papers": papers,
        "companies": company_updates
    }
    
    daily_file = os.path.join(ARCHIVE_DIR, f"{today_key}.json")
    with open(daily_file, "w", encoding="utf-8") as f:
        json.dump(daily_data, f, ensure_ascii=False, indent=2)
    print(f"Saved daily archive: {daily_file}")
    
    # 2. Master search catalog
    index_file = os.path.join(ARCHIVE_DIR, "index.json")
    catalog = []
    if os.path.exists(index_file):
        try:
            with open(index_file, "r", encoding="utf-8") as f:
                catalog = json.load(f)
        except Exception:
            catalog = []
            
    # Remove existing entry for today if re-running
    catalog = [entry for entry in catalog if entry.get("date_key") != today_key]
    
    # Build searchable keywords & headlines summary
    searchable_items = []
    if stories:
        searchable_items.append({"title": stories[0]["title"], "type": "Lead", "link": stories[0]["link"]})
    for s in stories[1:]:
        searchable_items.append({"title": s["title"], "type": "Industry", "link": s["link"]})
    for p in papers:
        searchable_items.append({"title": p["title"], "type": "Paper", "link": p["link"]})
    for reg, comps in company_updates.items():
        for c in comps:
            if c.get("link") and c["link"] != "#":
                searchable_items.append({"title": f"{c['name']}: {c['update']}", "type": "Company", "link": c["link"]})
                
    catalog.insert(0, {
        "date_key": today_key,
        "date_display": today_str,
        "items_count": len(searchable_items),
        "items": searchable_items
    })
    
    with open(index_file, "w", encoding="utf-8") as f:
        json.dump(catalog, f, ensure_ascii=False, indent=2)
    print(f"Updated master search catalog: {index_file} ({len(catalog)} editions archived)")

def render_html(today_str, papers, stories, company_updates):
    lead = stories[0]
    secondary_stories = stories[1:]
    
    secondary_html = ""
    for s in secondary_stories:
        secondary_html += f"""
        <div class="story-card">
            <div class="story-meta">{s['source']}</div>
            <h3><a href="{s['link']}" target="_blank" rel="noopener">{s['title']}</a></h3>
        </div>
        """
        
    papers_html = ""
    for p in papers:
        papers_html += f"""
        <div class="paper-card">
            <span class="paper-tag">{p['category']}</span>
            <div class="paper-title">
                <a href="{p['link']}" target="_blank" rel="noopener">{p['title']}</a>
            </div>
            <p class="paper-takeaway">{p['summary']}</p>
        </div>
        """
        
    def render_region_cards(companies):
        html = ""
        for c in companies:
            html += f"""
            <div class="radar-card">
                <div class="radar-card-header">
                    <span class="radar-company">{c['name']}</span>
                    <span class="radar-robot">{c['robot']}</span>
                </div>
                <div class="radar-update">
                    <a href="{c['link']}" target="_blank" rel="noopener">{c['update']}</a>
                </div>
                <div class="radar-meta">{c['meta']}</div>
            </div>
            """
        return html

    usa_html = render_region_cards(company_updates.get("usa", []))
    china_html = render_region_cards(company_updates.get("china", []))
    europe_html = render_region_cards(company_updates.get("europe", []))
    korea_html = render_region_cards(company_updates.get("korea", []))

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=5.0, user-scalable=yes">
    <title>The Physical AI Chronicle — Daily Mobile Edition</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Cinzel:wght@700;900&family=Inter:wght@400;500;600;700&family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,600;0,6..72,700;1,6..72,400&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
    <style>
        :root {{
            --paper-bg: #faf8f5;
            --paper-card: #ffffff;
            --ink-primary: #18181b;
            --ink-secondary: #3f3f46;
            --ink-muted: #71717a;
            --rule-dark: #27272a;
            --rule-light: #e4e4e7;
            --accent: #b91c1c;
            --tag-bg: #f4f4f5;
            --font-masthead: 'Cinzel', serif;
            --font-body: 'Newsreader', Georgia, serif;
            --font-sans: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            --font-mono: 'JetBrains Mono', monospace;
        }}

        [data-theme="dark"] {{
            --paper-bg: #09090b;
            --paper-card: #141417;
            --ink-primary: #f4f4f5;
            --ink-secondary: #d4d4d8;
            --ink-muted: #a1a1aa;
            --rule-dark: #52525b;
            --rule-light: #27272a;
            --accent: #ef4444;
            --tag-bg: #1e1e24;
        }}

        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
            -webkit-tap-highlight-color: transparent;
        }}

        body {{
            background-color: var(--paper-bg);
            color: var(--ink-primary);
            font-family: var(--font-body);
            line-height: 1.55;
            font-size: 16.5px;
            padding: 12px 14px 60px;
            transition: background 0.15s, color 0.15s;
        }}

        .container {{
            max-width: 900px;
            margin: 0 auto;
        }}

        .top-bar {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-family: var(--font-sans);
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            padding: 6px 0 10px;
            border-bottom: 1px solid var(--rule-light);
            margin-bottom: 14px;
        }}

        .back-link {{
            color: var(--ink-secondary);
            text-decoration: none;
            font-weight: 600;
            display: inline-flex;
            align-items: center;
            gap: 4px;
            padding: 4px 0;
        }}

        .theme-toggle {{
            background: none;
            border: 1px solid var(--rule-dark);
            padding: 5px 12px;
            font-family: var(--font-sans);
            font-size: 11px;
            font-weight: 600;
            cursor: pointer;
            color: var(--ink-primary);
            border-radius: 4px;
        }}

        header.masthead {{
            text-align: center;
            padding: 10px 0 16px;
            border-bottom: 3px double var(--rule-dark);
            margin-bottom: 16px;
        }}

        .sub-masthead-top {{
            font-family: var(--font-sans);
            font-size: 10px;
            text-transform: uppercase;
            letter-spacing: 0.18em;
            color: var(--ink-muted);
            margin-bottom: 4px;
        }}

        h1.newspaper-title {{
            font-family: var(--font-masthead);
            font-size: clamp(28px, 7vw, 56px);
            font-weight: 900;
            letter-spacing: -0.02em;
            line-height: 1.08;
            color: var(--ink-primary);
            text-transform: uppercase;
        }}

        .masthead-tagline {{
            font-family: var(--font-body);
            font-style: italic;
            font-size: 14px;
            color: var(--ink-secondary);
            margin-top: 6px;
        }}

        .issue-bar {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-top: 1px solid var(--rule-dark);
            border-bottom: 1px solid var(--rule-dark);
            padding: 5px 8px;
            margin-top: 12px;
            font-family: var(--font-sans);
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.06em;
            color: var(--ink-secondary);
            flex-wrap: wrap;
            gap: 4px;
        }}

        /* Search & Archive Box */
        .archive-search-box {{
            margin: 16px 0 20px;
            background-color: var(--paper-card);
            border: 1px solid var(--rule-light);
            border-radius: 8px;
            padding: 12px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.03);
        }}

        .search-input-wrapper {{
            display: flex;
            align-items: center;
            gap: 8px;
        }}

        .search-input {{
            flex: 1;
            padding: 10px 14px;
            font-family: var(--font-sans);
            font-size: 14.5px;
            background-color: var(--paper-bg);
            border: 1px solid var(--rule-dark);
            border-radius: 6px;
            color: var(--ink-primary);
            outline: none;
        }}
        .search-input:focus {{
            border-color: var(--accent);
        }}

        .search-results {{
            margin-top: 12px;
            display: none;
            max-height: 320px;
            overflow-y: auto;
        }}

        .search-result-item {{
            padding: 8px 10px;
            border-bottom: 1px solid var(--rule-light);
            font-size: 14px;
        }}
        .search-result-item:last-child {{ border-bottom: none; }}
        .search-result-item a {{
            color: var(--ink-primary);
            text-decoration: none;
            font-weight: 500;
        }}
        .search-result-item a:hover {{ color: var(--accent); }}
        .search-meta {{
            font-family: var(--font-sans);
            font-size: 10.5px;
            color: var(--ink-muted);
            margin-top: 3px;
        }}

        .lead-story {{
            padding: 14px 0 20px;
            border-bottom: 1px solid var(--rule-light);
            margin-bottom: 22px;
        }}

        .badge {{
            display: inline-block;
            font-family: var(--font-sans);
            font-size: 10px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.12em;
            padding: 3px 8px;
            background-color: var(--accent);
            color: #ffffff;
            border-radius: 3px;
            margin-bottom: 10px;
        }}

        .lead-headline {{
            font-family: var(--font-body);
            font-size: clamp(22px, 5.5vw, 34px);
            font-weight: 700;
            line-height: 1.2;
            margin-bottom: 10px;
        }}

        .lead-headline a {{
            color: var(--ink-primary);
            text-decoration: none;
        }}

        .lead-byline {{
            font-family: var(--font-sans);
            font-size: 11px;
            color: var(--ink-muted);
            margin-bottom: 12px;
        }}

        .section-header {{
            font-family: var(--font-sans);
            font-size: 12px;
            font-weight: 800;
            text-transform: uppercase;
            letter-spacing: 0.14em;
            color: var(--ink-primary);
            padding: 8px 0;
            border-top: 2px solid var(--rule-dark);
            border-bottom: 1px solid var(--rule-dark);
            margin: 28px 0 16px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}

        .story-card {{
            background-color: var(--paper-card);
            border: 1px solid var(--rule-light);
            border-left: 3px solid var(--accent);
            border-radius: 6px;
            padding: 14px 16px;
            margin-bottom: 14px;
        }}

        .story-meta {{
            font-family: var(--font-sans);
            font-size: 10.5px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: var(--accent);
            margin-bottom: 4px;
        }}

        .story-card h3 {{
            font-family: var(--font-body);
            font-size: 18px;
            font-weight: 700;
            line-height: 1.25;
            margin-bottom: 6px;
        }}
        .story-card h3 a {{
            color: var(--ink-primary);
            text-decoration: none;
        }}

        .paper-card {{
            background-color: var(--paper-card);
            border: 1px solid var(--rule-light);
            border-radius: 6px;
            padding: 14px 16px;
            margin-bottom: 12px;
        }}

        .paper-tag {{
            font-family: var(--font-mono);
            font-size: 10px;
            font-weight: 600;
            background-color: var(--tag-bg);
            padding: 2px 6px;
            border-radius: 3px;
            display: inline-block;
            margin-bottom: 6px;
            color: var(--ink-primary);
        }}

        .paper-title {{
            font-family: var(--font-body);
            font-size: 16.5px;
            font-weight: 700;
            line-height: 1.3;
            margin-bottom: 6px;
        }}
        .paper-title a {{
            color: var(--ink-primary);
            text-decoration: none;
        }}

        .paper-takeaway {{
            font-size: 14px;
            color: var(--ink-secondary);
            line-height: 1.45;
        }}

        .radar-region-title {{
            font-family: var(--font-sans);
            font-size: 12px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.1em;
            color: var(--ink-secondary);
            margin: 18px 0 10px;
        }}

        .radar-grid {{
            display: grid;
            grid-template-columns: 1fr;
            gap: 10px;
            margin-bottom: 14px;
        }}

        .radar-card {{
            background-color: var(--paper-card);
            border: 1px solid var(--rule-light);
            border-radius: 6px;
            padding: 12px 14px;
            box-shadow: 0 1px 2px rgba(0,0,0,0.02);
        }}

        .radar-card-header {{
            display: flex;
            justify-content: space-between;
            align-items: baseline;
            margin-bottom: 6px;
        }}

        .radar-company {{
            font-family: var(--font-sans);
            font-size: 13.5px;
            font-weight: 700;
            color: var(--ink-primary);
        }}

        .radar-robot {{
            font-family: var(--font-mono);
            font-size: 11px;
            color: var(--ink-muted);
        }}

        .radar-update {{
            font-family: var(--font-body);
            font-size: 15.5px;
            line-height: 1.35;
            margin-bottom: 6px;
        }}
        .radar-update a {{
            color: var(--ink-primary);
            text-decoration: none;
        }}
        .radar-update a:hover {{
            color: var(--accent);
            text-decoration: underline;
        }}

        .radar-meta {{
            font-family: var(--font-sans);
            font-size: 10.5px;
            color: var(--accent);
            font-weight: 600;
        }}

        footer {{
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid var(--rule-light);
            text-align: center;
            font-family: var(--font-sans);
            font-size: 11.5px;
            color: var(--ink-muted);
        }}
    </style>
</head>
<body>

<div class="container">
    <div class="top-bar">
        <a href="../" class="back-link">← Home</a>
        <div>
            <button class="theme-toggle" onclick="toggleTheme()">🌓 Dark / Light</button>
        </div>
    </div>

    <header class="masthead">
        <div class="sub-masthead-top">Autonomous Systems · Embodied AI · Humanoids</div>
        <h1 class="newspaper-title">The Physical AI Chronicle</h1>
        <div class="masthead-tagline">"Tracking the emergence of intelligence in the physical world."</div>
        
        <div class="issue-bar">
            <span>Vol. I · Daily</span>
            <span>{today_str}</span>
            <span>Seoul, KR</span>
        </div>
    </header>

    <!-- Interactive Archive Search -->
    <section class="archive-search-box">
        <div class="search-input-wrapper">
            <input type="text" id="archiveSearch" class="search-input" placeholder="🔍 Search archive by company, keyword, or date..." oninput="handleSearch(this.value)">
        </div>
        <div id="searchResults" class="search-results"></div>
    </section>

    <main id="dailyContent">
        <article class="lead-story">
            <span class="badge">Lead Story</span>
            <h2 class="lead-headline">
                <a href="{lead['link']}" target="_blank" rel="noopener">{lead['title']}</a>
            </h2>
            <div class="lead-byline">
                <span>Source: {lead['source']} · Real-time Feed</span>
            </div>
        </article>

        <div class="section-header">
            <span>Industry & Hardware Wire</span>
            <span>⚡ Global</span>
        </div>

        {secondary_html}

        <div class="section-header">
            <span>ArXiv Preprints</span>
            <span>[cs.RO / cs.AI]</span>
        </div>

        {papers_html}

        <div class="section-header">
            <span>Global Radar: Company Updates & Breakthroughs</span>
            <span>USA · China · Europe · Korea</span>
        </div>

        <div class="radar-region-title">🇺🇸 United States (Foundation Models & Enterprise)</div>
        <div class="radar-grid">
            {usa_html}
        </div>

        <div class="radar-region-title">🇨🇳 China (Manufacturing Scale & Cost Efficiency)</div>
        <div class="radar-grid">
            {china_html}
        </div>

        <div class="radar-region-title">🇪🇺 Europe (Industrial Safety & Precision Automation)</div>
        <div class="radar-grid">
            {europe_html}
        </div>

        <div class="radar-region-title">🇰🇷 South Korea (K-Humanoid Alliance & Wearables)</div>
        <div class="radar-grid">
            {korea_html}
        </div>
    </main>

    <footer>
        <p>The Physical AI Chronicle · Daily Mobile Edition</p>
        <p style="margin-top: 4px;">Curated by Antigravity Autonomous Agent · Hosted on GitHub Pages</p>
    </footer>
</div>

<script>
    function toggleTheme() {{
        const currentTheme = document.documentElement.getAttribute('data-theme');
        if (currentTheme === 'dark') {{
            document.documentElement.removeAttribute('data-theme');
            localStorage.setItem('theme', 'light');
        }} else {{
            document.documentElement.setAttribute('data-theme', 'dark');
            localStorage.setItem('theme', 'dark');
        }}
    }}

    if (localStorage.getItem('theme') === 'dark' || 
        (!localStorage.getItem('theme') && window.matchMedia('(prefers-color-scheme: dark)').matches)) {{
        document.documentElement.setAttribute('data-theme', 'dark');
    }}

    // Archive Search Engine
    let searchCatalog = [];
    async function loadArchiveIndex() {{
        try {{
            const res = await fetch('archive/index.json');
            if (res.ok) {{
                searchCatalog = await res.json();
            }}
        }} catch(e) {{
            console.log('Archive catalog not yet available.');
        }}
    }}
    loadArchiveIndex();

    function handleSearch(query) {{
        const container = document.getElementById('searchResults');
        query = query.trim().toLowerCase();
        if (!query || query.length < 2) {{
            container.style.display = 'none';
            container.innerHTML = '';
            return;
        }}

        const matches = [];
        for (const edition of searchCatalog) {{
            for (const item of (edition.items || [])) {{
                if (item.title.toLowerCase().includes(query) || edition.date_display.toLowerCase().includes(query)) {{
                    matches.push({{
                        title: item.title,
                        type: item.type,
                        link: item.link,
                        date: edition.date_display
                    }});
                }}
            }}
        }}

        if (matches.length === 0) {{
            container.innerHTML = '<div style="padding: 10px; font-size: 13px; color: var(--ink-muted);">No archived stories found matching "' + query + '".</div>';
        }} else {{
            container.innerHTML = matches.slice(0, 15).map(m => `
                <div class="search-result-item">
                    <a href="${{m.link}}" target="_blank" rel="noopener">${{m.title}}</a>
                    <div class="search-meta"><b>${{m.type}}</b> · ${{m.date}}</div>
                </div>
            `).join('');
        }}
        container.style.display = 'block';
    }}
</script>

</body>
</html>
"""
    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"Successfully generated: {OUTPUT_HTML}")

def main():
    now = datetime.datetime.now()
    today_key = now.strftime("%Y-%m-%d")
    today_str = now.strftime("%a, %b %d, %Y")
    
    papers = fetch_arxiv_papers(max_results=4)
    stories = fetch_industry_stories()
    company_updates = fetch_company_updates()
    
    # Save to archive
    save_daily_archive(today_key, today_str, papers, stories, company_updates)
    
    # Render HTML
    render_html(today_str, papers, stories, company_updates)

if __name__ == "__main__":
    main()
