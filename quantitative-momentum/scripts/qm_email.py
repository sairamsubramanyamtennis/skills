#!/usr/bin/env python3
"""Send QM Screener results via Gmail SMTP with Excel attachment.

Usage:
    python qm_email.py <excel_file> [--screener-csv <csv_file>] [--to <email>]

The script:
1. Reads the top 10 stocks from the screener CSV (if provided) for the email body
2. Attaches the Excel file
3. Sends via Gmail SMTP using credentials from keyring (Windows Credential Manager)

Credential setup (one-time):
    python -c "import keyring; keyring.set_password('qm-screener-smtp', 'ssairam@gmail.com', 'YOUR_APP_PASSWORD')"

Fallback: If keyring is unavailable, set environment variable GMAIL_APP_PASSWORD.
"""

import argparse
import csv
import os
import smtplib
import sys
from datetime import datetime
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

SENDER = "ssairam@gmail.com"
DEFAULT_RECIPIENT = "ssairam@gmail.com"
KEYRING_SERVICE = "qm-screener-smtp"
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587


def get_password(sender):
    try:
        import keyring
        pw = keyring.get_password(KEYRING_SERVICE, sender)
        if pw:
            return pw
    except Exception:
        pass
    pw = os.environ.get("GMAIL_APP_PASSWORD")
    if pw:
        return pw
    print("ERROR: No Gmail app password found. Set it via keyring or GMAIL_APP_PASSWORD env var.", file=sys.stderr)
    sys.exit(1)


def read_top_stocks(csv_path, n=10):
    if not csv_path or not Path(csv_path).exists():
        return []
    stocks = []
    with open(csv_path, newline="") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            if i >= n:
                break
            stocks.append({
                "rank": row.get("Rank", row.get("rank", i + 1)),
                "ticker": row.get("Ticker", row.get("ticker", "")),
                "company": row.get("Company", row.get("company", "")),
                "signal": row.get("Signal", row.get("signal", "")),
                "vol_adj": row.get("6-1M VolAdj", row.get("6-1M Return%", row.get("vol_adj_momentum", ""))),
            })
    return stocks


def build_html_body(stocks, excel_filename, analysis_date):
    top_rows = ""
    for s in stocks:
        vol_adj = s["vol_adj"]
        try:
            val = float(vol_adj)
            vol_adj = f"{val:.2f}"
        except (ValueError, TypeError):
            pass
        top_rows += f"""<tr>
            <td style="padding:4px 8px;border:1px solid #ddd;text-align:center">{s['rank']}</td>
            <td style="padding:4px 8px;border:1px solid #ddd;font-weight:bold">{s['ticker']}</td>
            <td style="padding:4px 8px;border:1px solid #ddd">{s['company']}</td>
            <td style="padding:4px 8px;border:1px solid #ddd;text-align:center">{s['signal']}</td>
            <td style="padding:4px 8px;border:1px solid #ddd;text-align:right">{vol_adj}</td>
        </tr>"""

    table_html = ""
    if top_rows:
        table_html = f"""
        <h3 style="color:#1F4E79;margin-top:16px">Top 10 Momentum Stocks</h3>
        <table style="border-collapse:collapse;font-family:Arial,sans-serif;font-size:13px">
            <thead>
                <tr style="background:#1F4E79;color:white">
                    <th style="padding:6px 8px;border:1px solid #ddd">Rank</th>
                    <th style="padding:6px 8px;border:1px solid #ddd">Ticker</th>
                    <th style="padding:6px 8px;border:1px solid #ddd">Company</th>
                    <th style="padding:6px 8px;border:1px solid #ddd">Signal</th>
                    <th style="padding:6px 8px;border:1px solid #ddd">6-1M VolAdj</th>
                </tr>
            </thead>
            <tbody>{top_rows}</tbody>
        </table>"""

    return f"""<html><body style="font-family:Arial,sans-serif;color:#333;line-height:1.5">
    <p>Here are today's Quantitative Momentum screener results.</p>
    <p><strong>Date:</strong> {analysis_date}<br>
    <strong>File:</strong> {excel_filename}</p>
    {table_html}
    <p style="margin-top:16px;color:#666;font-size:12px">
        Full results including all ~500 S&amp;P 500 stocks, sector breakdown, and momentum decay
        warnings are in the attached Excel workbook.
    </p>
    <p style="color:#666;font-size:11px">— QM Screener (automated)</p>
    </body></html>"""


def send_email(to, subject, html_body, excel_path, sender, password):
    msg = MIMEMultipart()
    msg["From"] = sender
    msg["To"] = to
    msg["Subject"] = subject
    msg.attach(MIMEText(html_body, "html"))

    with open(excel_path, "rb") as f:
        att = MIMEApplication(f.read(), _subtype="vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        att.add_header("Content-Disposition", "attachment", filename=Path(excel_path).name)
        msg.attach(att)

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(sender, password)
        server.send_message(msg)

    print(f"Email sent to {to} with attachment {Path(excel_path).name}")


def main():
    parser = argparse.ArgumentParser(description="Email QM Screener results via Gmail SMTP")
    parser.add_argument("excel_file", help="Path to the Excel workbook to attach")
    parser.add_argument("--screener-csv", help="Path to screener CSV for top-10 summary in email body")
    parser.add_argument("--to", default=DEFAULT_RECIPIENT, help="Recipient email address")
    args = parser.parse_args()

    excel_path = Path(args.excel_file)
    if not excel_path.exists():
        print(f"ERROR: Excel file not found: {excel_path}", file=sys.stderr)
        sys.exit(1)

    password = get_password(SENDER)
    stocks = read_top_stocks(args.screener_csv)
    analysis_date = datetime.now().strftime("%B %d, %Y")
    subject = f"QM Screener Results — {analysis_date}"
    html_body = build_html_body(stocks, excel_path.name, analysis_date)

    send_email(args.to, subject, html_body, str(excel_path), SENDER, password)


if __name__ == "__main__":
    main()
