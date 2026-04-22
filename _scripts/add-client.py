"""Generate a new client portal page from the template.

Usage:
    python3 _scripts/add-client.py

Then follow the prompts, OR edit clients.csv and run:
    python3 _scripts/add-client.py --csv

Each run:
  1. Reads template from _template/client.html
  2. Replaces placeholders with client-specific values
  3. Writes /clients/{slug}/index.html
  4. Updates the CLIENT_MAP in /index.html to route that email to the slug
  5. Reminds you to add the email to Cloudflare Access policy
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


def generate_client_page(data: dict):
    """Build a client's index.html from the template."""
    with open(TEMPLATE_PATH, encoding="utf-8") as f:
        template = f.read()

    first_name = data["client_name"].split()[0]
    replacements = {
        "{{CLIENT_NAME}}": data["client_name"],
        "{{CLIENT_FIRST_NAME}}": first_name,
        "{{REPORTS_URL}}": data.get("reports_url", "#"),
        "{{UPLOAD_URL}}": data.get("upload_url", "#"),
        "{{PUZZLE_URL}}": data.get("puzzle_url", "#"),
        "{{PAYROLL_URL}}": data.get("payroll_url", "#"),
    }

    content = template
    for placeholder, value in replacements.items():
        content = content.replace(placeholder, value)

    # If no payroll, hide the payroll card
    if not data.get("payroll_url") or data["payroll_url"].strip() == "":
        content = re.sub(
            r'<div class="integration-card" id="payroll-card">.*?</div>\s*</div>',
            '',
            content,
            flags=re.DOTALL,
            count=1
        )

    client_dir = CLIENTS_DIR / data["slug"]
    client_dir.mkdir(parents=True, exist_ok=True)
    out_path = client_dir / "index.html"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  ✓ Wrote {out_path.relative_to(ROOT)}")


def update_client_map(clients: list):
    """Rewrite the CLIENT_MAP in /index.html based on the clients list."""
    with open(INDEX_PATH, encoding="utf-8") as f:
        content = f.read()

    lines = [f'    "{c["email"].lower()}": "{c["slug"]}",' for c in clients]
    new_map = "  const CLIENT_MAP = {\n    // email → client slug (auto-generated — do not edit manually)\n" + "\n".join(lines) + "\n  };"

    new_content = re.sub(
        r'const CLIENT_MAP = \{.*?\};',
        new_map.replace("  const CLIENT_MAP", "const CLIENT_MAP"),
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
    data["puzzle_url"] = input("  Puzzle.io dashboard URL: ").strip() or "#"
    data["payroll_url"] = input("  Gusto payroll URL (leave blank if not enrolled): ").strip()
    return data


def append_to_csv(data: dict):
    """Add a client row to clients.csv. Creates the file if missing."""
    fieldnames = ["slug", "client_name", "email", "reports_url", "upload_url", "puzzle_url", "payroll_url"]
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

    print(f"""
✅ Done.

Next steps:
1. Add this client's email to Cloudflare Access:
   Dashboard → Zero Trust → Access → Applications → tides-portal
   → Policies → Edit 'Allow clients' → Add email
2. Commit and push:
   git add -A && git commit -m "Add client: {clients[-1]['client_name'] if clients else ''}" && git push
3. Send client their portal URL:
   https://portal.tidesbookkeeping.com
   (They'll be prompted to enter their email → get a code → auto-redirect to their portal)
""")


if __name__ == "__main__":
    main()
