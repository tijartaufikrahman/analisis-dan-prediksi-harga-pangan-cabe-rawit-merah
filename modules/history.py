import os
import pandas as pd
from flask import Blueprint, render_template, jsonify, request

history_bp = Blueprint("history", __name__)

DATA_FOLDER = "data"

# =========================
# UI HISTORY
# =========================
@history_bp.route("/history/")
def history_page():
    return render_template("data-history.html")


# =========================
# API GET FILES
# =========================
@history_bp.route("/api/history/files")
def api_history_files():

    if not os.path.exists(DATA_FOLDER):
        return jsonify([])

    files = [
        f for f in os.listdir(DATA_FOLDER)
        if f.lower().endswith(".csv")
    ]

    return jsonify(files)


# =========================
# API LOAD DATA
# =========================
@history_bp.route("/api/history/load", methods=["POST"])
def api_history_load():

    data = request.json
    filename = data.get("file")
    mode = data.get("mode", "bulanan")  # default bulanan

    if not filename:
        return jsonify({
            "success": False,
            "message": "File belum dipilih"
        })

    path = os.path.join(DATA_FOLDER, filename)

    if not os.path.exists(path):
        return jsonify({
            "success": False,
            "message": "File tidak ditemukan"
        })

    try:
        df = pd.read_csv(path, sep=";")
        df.columns = df.columns.str.strip()

        # =========================
        # MODE HARIAN (FULL CSV)
        # =========================
        if mode == "harian":

            df = df.fillna("")

            return jsonify({
                "success": True,
                "mode": "harian",
                "columns": df.columns.tolist(),
                "data": df.to_dict(orient="records")
            })

        # =========================
        # MODE BULANAN (DEFAULT)
        # =========================
        if "Tanggal" not in df.columns or "Harga (Rp)" not in df.columns:
            return jsonify({
                "success": False,
                "message": "Kolom tidak sesuai"
            })

        df["Tanggal"] = pd.to_datetime(
            df["Tanggal"],
            dayfirst=True,
            errors="coerce"
        )

        df = df.dropna(subset=["Tanggal"])
        df = df.set_index("Tanggal")

        df_bulanan = (
            df["Harga (Rp)"]
            .resample("ME")
            .mean()
            .round(0)
            .astype(int)
        )

        df_bulanan = df_bulanan.to_frame(name="Harga")
        df_bulanan["Bulan"] = df_bulanan.index.strftime("%m/%Y")
        df_bulanan = df_bulanan.reset_index(drop=True)

        # Atur urutan kolom
        df_bulanan = df_bulanan[["Bulan", "Harga"]]


        return jsonify({
            "success": True,
            "mode": "bulanan",
            "columns": df_bulanan.columns.tolist(),
            "data": df_bulanan.to_dict(orient="records")
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        })
