"""Generate a new client portal page from the template.

Usage:
    python3 _scripts/add-client.py             # interactive
    python3 _scripts/add-client.py --csv       # rebuild ALL clients from clients.csv

Each run:
  1. Reads template from _template/client.html
  2. Replaces placeholders with client-specific values
  3. Writes /clients/{slug}/index.html
  4. Updates the CLIENT_MAP in /index.html to route email → slug
  5. Reminds you to add the email to Cloudflare Access policy

CSV FORMAT — _scripts/clients.csv:
    slug,client_name,email,reports_url,upload_url,quick_links

  The 'quick_links' column is a list of links separated by ';' (semicolons),
  each link formatted as 'Label|URL'. Example:

    "QuickBooks Online|https://qbo.intuit.com/app/123;Puzzle Dashboard|https://puzzle.io/a/abc;Annual Tax Filings|https://onedrive.live.com/foo"

  Use double-quotes around the column to keep commas inside URLs from
  breaking CSV parsing.

ICONS — Default icons are matched by label keyword (case-insensitive). Add
your own to QUICK_LINK_ICONS below to customize.
"""

import os
import re
import sys
import csv
from pathlib import Path

ROOT = Path(__file__).parent.parent
TEMPLATE_PATH = ROOT / "_template" / "client.html"
CLIENTS_DIR = ROOT / "clients"
INDEX_PATH = ROOT / "index.html"
CSV_PATH = ROOT / "_scripts" / "clients.csv"


# ─── Icon mapping for Quick Links ────────────────────────────
# Match by keyword in label (case-insensitive). First match wins.
QUICK_LINK_ICONS = [
    ("quickbooks",   {"icon": "📊", "bg": "#e7f5ee", "fg": "#1a8a4d"}),
    ("puzzle",       {"icon": "🧩", "bg": "#f0eefd", "fg": "#5b47fb"}),
    ("tax",          {"icon": "📑", "bg": "#fef3c7", "fg": "#d97706"}),
    ("payroll",      {"icon": "💰", "bg": "#fef3c7", "fg": "#d97706"}),
    ("gusto",        {"icon": "💰", "bg": "#fef3c7", "fg": "#d97706"}),
    ("bank",         {"icon": "🏦", "bg": "#e8f4fd", "fg": "#1565c0"}),
    ("stripe",       {"icon": "💳", "bg": "#f0f0ff", "fg": "#635bff"}),
    ("calendar",     {"icon": "📅", "bg": "#fce8e6", "fg": "#c5221f"}),
    ("dashboard",    {"icon": "📈", "bg": "#e6f9f9", "fg": "#0d8585"}),
    ("default",      {"icon": "🔗", "bg": "#e8f4fd", "fg": "#1565c0"}),
]


def icon_for(label: str) -> dict:
    low = label.lower()
    for key, style in QUICK_LINK_ICONS:
        if key != "default" and key in low:
            return style
    return dict([s for s in QUICK_LINK_ICONS if s[0] == "default"][0][1].items())


def parse_quick_links(raw: str) -> list[dict]:
    """Parse 'Label|URL;Label|URL' format into a list of dicts."""
    if not raw or raw.strip() == "":
        return []
    items = []
    for piece in raw.split(";"):
        piece = piece.strip()
        if not piece or "|" not in piece:
            continue
        label, _, url = piece.partition("|")
        label = label.strip()
        url = url.strip()
        if label and url:
            items.append({"label": label, "url": url})
    return items


def render_quick_links_html(links: list[dict]) -> str:
    """Build the HTML for the Quick Links cards section."""
    if not links:
        return '<p style="color:var(--muted);text-align:center;padding:2rem;font-size:.92rem;">No quick links configured.</p>'
    cards = []
    for link in links:
        style = icon_for(link["label"])
        # Determine button text from label
        verb = "Open" if "dashboard" not in link["label"].lower() else "Open"
        cards.append(f'''      <div class="integration-card">
        <div class="header">
          <div class="logo-box" style="background:{style['bg']};color:{style['fg']};">{style['icon']}</div>
          <div>
            <h3>{link['label']}</h3>
          </div>
        </div>
        <a href="{link['url']}" target="_blank" class="btn btn-primary">{verb} →</a>
      </div>''')
    return "\n".join(cards)


def generate_client_page(data: dict):
    """Build a client's index.html from the template."""
    with open(TEMPLATE_PATH, encoding="utf-8") as f:
        template = f.read()

    first_name = data["client_name"].split()[0]
    quick_links = parse_quick_links(data.get("quick_links", ""))

    replacements = {
        "{{CLIENT_NAME}}": data["client_name"],
        "{{CLIENT_FIRST_NAME}}": first_name,
        "{{REPORTS_URL}}": data.get("reports_url", "#") or "#",
        "{{UPLOAD_URL}}": data.get("upload_url", "#") or "#",
        "{{QUICK_LINKS_HTML}}": render_quick_links_html(quick_links),
    }

    content = template
    for placeholder, value in replacements.items():
        content = content.replace(placeholder, value)

    client_dir = CLIENTS_DIR / data["slug"]
    client_dir.mkdir(parents=True, exist_ok=True)
    out_path = client_dir / "index.html"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  ✓ Wrote {out_path.relative_to(ROOT)} ({len(quick_links)} quick links)")


def update_client_map(clients: list):
    """Rewrite the CLIENT_MAP in /index.html based on the clients list."""
    with open(INDEX_PATH, encoding="utf-8") as f:
        content = f.read()

    lines = [f'    "{c["email"].lower()}": "{c["slug"]}",' for c in clients]
    new_map = "const CLIENT_MAP = {\n    // email → client slug (auto-generated — do not edit manually)\n" + "\n".join(lines) + "\n  };"

    new_content = re.sub(
        r'const CLIENT_MAP = \{.*?\};',
        new_map,
        content,
        flags=re.DOTALL,
        count=1
    )
    with open(INDEX_PATH, "w", encoding="utf-8") as f:
        f.write(new_content)
    print(f"  ✓ Updated email→slug routing in index.html ({len(clients)} clients)")


def read_csv():
    """Read clients.csv. Returns list of dicts."""
    if not CSV_PATH.exists():
        return []
    clients = []
    with open(CSV_PATH, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("slug") and row.get("email"):
                clients.append(row)
    return clients


def prompt_client():
    """Interactive: prompt for a new client's data."""
    print("\nAdd a new client to the portal:\n")
    data = {}
    data["client_name"] = input("  Client name (e.g., 'Acme Corp'): ").strip()
    slug_default = re.sub(r'[^a-z0-9]+', '-', data["client_name"].lower()).strip('-')
    slug = input(f"  URL slug [{slug_default}]: ").strip() or slug_default
    data["slug"] = slug
    data["email"] = input("  Client email (login): ").strip()
    data["reports_url"] = input("  OneDrive Reports folder share link: ").strip() or "#"
    data["upload_url"] = input("  OneDrive Request Files upload link: ").strip() or "#"
    print("\n  Quick links — enter Label|URL pairs separated by ';' (semicolons).")
    print("  Example: QuickBooks Online|https://qbo.intuit.com/app/123;Puzzle Dashboard|https://puzzle.io/a/abc")
    print("  Leave blank to skip.")
    data["quick_links"] = input("  Quick links: ").strip()
    return data


def append_to_csv(data: dict):
    """Add a client row to clients.csv. Creates the file if missing."""
    fieldnames = ["slug", "client_name", "email", "reports_url", "upload_url", "quick_links"]
    is_new = not CSV_PATH.exists()
    with open(CSV_PATH, "a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if is_new:
            writer.writeheader()
        writer.writerow({k: data.get(k, "") for k in fieldnames})


def main():
    use_csv = "--csv" in sys.argv

    if use_csv:
        clients = read_csv()
        if not clients:
            print(f"No clients found in {CSV_PATH}. Add rows and re-run.")
            sys.exit(1)
        print(f"\nBuilding {len(clients)} client portal(s) from CSV:\n")
        for c in clients:
            print(f"• {c['client_name']} ({c['email']}) → /clients/{c['slug']}/")
            generate_client_page(c)
        update_client_map(clients)
    else:
        data = prompt_client()
        print(f"\nBuilding portal for {data['client_name']}...\n")
        generate_client_page(data)
        append_to_csv(data)
        clients = read_csv()
        update_client_map(clients)

    last_name = clients[-1]['client_name'] if clients else ''
    print(f"""
✅ Done.

Next steps:
1. Add this client's email to Cloudflare Access:
   Dashboard → Zero Trust → Access → Applications → tides-portal
   → Policies → Edit 'Allow clients' → Add email
2. Commit and push:
   git add -A && git commit -m "Add client: {last_name}" && git push
3. Send the client their portal URL:
   https://portal.tidesbookkeeping.com
   (They'll be prompted to enter their email → get a 6-digit code → auto-redirect to their portal)
""")


if __name__ == "__main__":
    main()
