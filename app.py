from flask import Flask, render_template, request, send_from_directory, url_for
import pandas as pd
import os
from datetime import datetime
import pytz
import re

app = Flask(__name__)

UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Updated Client list based on your specific needs
CLIENTS = {
    "johnson": "Mike Johnson for Louisiana",
    "britt": "Britt for Alabama Inc",
    "daf": "Defending Americas Future",
    "rogers": "Rogers for Senate",
    "hilton": "Steve Hilton for Governor 2026",
    "whatley": "Whatley for Senate",
    "afw": "America First Works"
}

def clean_filename(name):
    return re.sub(r"[^A-Za-z0-9_-]", "", name.replace(" ", "_"))

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        client_key = request.form.get("client")
        org_name = CLIENTS.get(client_key, "Mike Johnson for Louisiana")
        file = request.files["file"]

        if not file or file.filename == "":
            return "No file selected", 400

        # Save uploaded file
        input_filename = f"upload_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        input_path = os.path.join(UPLOAD_FOLDER, input_filename)
        file.save(input_path)

        try:
            # --- CONDUIT PROCESSING LOGIC ---
            mj = pd.read_csv(input_path)
            
            # 1. Clean Data
            mj = mj[mj['Status'] == 'succeeded'].copy()
            mj['Created At'] = pd.to_datetime(mj['Created At'], format='mixed', utc=True).dt.tz_convert('US/Eastern')
            
            # 2. Filter Conduits and Calculate Totals
            conduit_amts = mj[mj['Source Name'] != org_name].copy()
            conduit_amts['Total Amount'] = conduit_amts['Processing Fees'] / 0.04
            
            # 3. Dynamic Quarters
            conduit_amts['Quarter_Period'] = conduit_amts['Created At'].dt.to_period('Q')
            
            quarters_pivot = conduit_amts.pivot_table(
                index='Source Name', 
                columns='Quarter_Period', 
                values='Total Amount', 
                aggfunc='sum',
                fill_value=0
            )
            
            # Format column names to "Q1 24"
            quarters_pivot.columns = [f"Q{q.quarter} {str(q.year)[2:]}" for q in quarters_pivot.columns]
            
            # 4. Aggregation
            other_metrics = conduit_amts.groupby('Source Name').agg({
                'Processing Fees': 'sum',
                'Revv Uid': 'count',
                'Total Amount': 'sum'
            })
            
            final_output = other_metrics.join(quarters_pivot).reset_index()
            
            # Organize Columns
            quarter_cols = list(quarters_pivot.columns)
            column_order = ['Source Name', 'Processing Fees'] + quarter_cols + ['Revv Uid', 'Total Amount']
            final_output = final_output[column_order]

            # Save Output
            output_filename = f"conduit_totals_{clean_filename(org_name)}_{datetime.now().strftime('%Y%m%d')}.csv"
            output_path = os.path.join(UPLOAD_FOLDER, output_filename)
            final_output.to_csv(output_path, index=False)

        finally:
            # Remove the uploaded input file immediately after processing
            if os.path.exists(input_path):
                os.remove(input_path)

        download_url = url_for("download_file", filename=output_filename)
        return render_template("index.html", status="ready", download_url=download_url)

    return render_template("index.html", status=None)

@app.route("/download/<filename>")
def download_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

if __name__ == "__main__":
    app.run(debug=True)
