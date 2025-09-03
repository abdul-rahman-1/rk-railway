import os
from datetime import datetime, timedelta, timezone
from flask import Flask, render_template, request, redirect, url_for, flash
from pymongo import MongoClient
from dotenv import load_dotenv
import cv2
import tempfile

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "change-me")

# MongoDB connection
client = MongoClient(os.getenv("MONGO_URI"))
db = client[os.getenv("MONGO_DB")]
collection = db[os.getenv("MONGO_COLLECTION")]

# ---------- Utility Functions ----------
def parse_date(date_str):
    """Convert ISO string to datetime object (always aware)."""
    if not date_str:
        return None
    dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt

def format_date(dt):
    return dt.strftime("%Y-%m-%d") if dt else "N/A"

# ---------- Routes ----------
@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        unique_id = request.form.get("unique_id")

        if "qr_file" in request.files and request.files["qr_file"].filename != "":
            file = request.files["qr_file"]

            # Create temp file
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
            file.save(temp_file.name)
            temp_file.close()  # ✅ Close so cv2 can access it

            # Now OpenCV can read it
            img = cv2.imread(temp_file.name)
            detector = cv2.QRCodeDetector()
            data, bbox, _ = detector.detectAndDecode(img)

            os.unlink(temp_file.name)  # ✅ Delete after reading

            if data:
                unique_id = data.strip()
        
        if unique_id:
            record = collection.find_one({"unique_id": unique_id})
            if record:
                return redirect(url_for("view_record", unique_id=unique_id))
            else:
                flash("No record found.", "danger")
                return redirect(url_for("home"))

    return render_template("home.html")

@app.route("/scan_qr")
def scan_qr():
    cap = cv2.VideoCapture(0)
    detector = cv2.QRCodeDetector()

    unique_id = None
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        data, bbox, _ = detector.detectAndDecode(frame)
        cv2.imshow("QR Scanner - Press Q to exit", frame)

        if data:
            unique_id = data.strip()
            break

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()

    if unique_id:
        record = collection.find_one({"unique_id": unique_id})
        if record:
            return redirect(url_for("view_record", unique_id=unique_id))
        else:
            flash("No record found for this QR.", "danger")
            return redirect(url_for("home"))
    else:
        flash("No QR detected.", "warning")
        return redirect(url_for("home"))

@app.route("/view/<unique_id>")
def view_record(unique_id):
    record = collection.find_one({"unique_id": unique_id})
    if not record:
        flash("Record not found.", "danger")
        return redirect(url_for("home"))

    # Convert date fields
    for field in ["DOM", "DOI", "expiry_date", "warrenty_date", "last_inspection_date", "next_inspection_date"]:
        if record.get(field):
            record[field] = format_date(parse_date(record[field]))
        else:
            record[field] = None

    # Flags
    today = datetime.now(timezone.utc)
    expiry_dt = parse_date(record.get("expiry_date"))
    warranty_dt = parse_date(record.get("warrenty_date"))

    record["expired"] = expiry_dt and expiry_dt < today
    record["warranty_over"] = warranty_dt and warranty_dt < today

    return render_template("view.html", record=record)

@app.route("/install/<unique_id>", methods=["POST"])
def install(unique_id):
    today = datetime.now(timezone.utc)
    next_inspection = today + timedelta(days=182)  # ~6 months
    collection.update_one(
        {"unique_id": unique_id},
        {"$set": {
            "DOI": today.isoformat(),
            "next_inspection_date": next_inspection.isoformat()
        }}
    )
    flash("Installation marked complete. Next inspection scheduled.", "success")
    return redirect(url_for("view_record", unique_id=unique_id))

@app.route("/inspect/<unique_id>", methods=["GET", "POST"])
def inspect(unique_id):
    record = collection.find_one({"unique_id": unique_id})
    if not record:
        flash("Record not found.", "danger")
        return redirect(url_for("home"))

    if request.method == "POST":
        # Get new health from form
        health = request.form.get("health")
        now = datetime.now(timezone.utc)
        next_inspection = now + timedelta(days=182)  # 6 months

        # Update MongoDB
        collection.update_one(
            {"unique_id": unique_id},
            {"$set": {
                "health": health,
                "last_inspection_date": now.isoformat(),
                "next_inspection_date": next_inspection.isoformat()
            }}
        )

        flash("Inspection updated successfully.", "success")
        return redirect(url_for("view_record", unique_id=unique_id))

    # Render inspection page
    return render_template("inspect.html", record=record)


if __name__ == "__main__":
    app.run(debug=True, port=int(os.getenv("PORT", 5000)))
