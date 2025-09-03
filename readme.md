# Railway App - Flask + QR Code Scanner

This is a **Flask application** for managing railway-related data. The app can **open the camera**, scan a **QR code**, decode it using **OpenCV**, fetch the corresponding data from **MongoDB**, and allow updates to the database.

---

## 🚀 Features

* Open **camera** to scan QR codes.
* Decode QR using **OpenCV (cv2)**.
* Fetch complete record from **MongoDB** using the scanned serial.
* Update the database with new values.
* Simple REST API for interaction.

---

## 🛠️ Tech Stack

* **Flask** (Python web framework)
* **MongoDB Atlas** (Database)
* **pymongo** (MongoDB driver)
* **python-dotenv** (Environment variables)
* **opencv-python (cv2)** (QR scanner)
* **qrcode** (QR code generator, optional for testing)

---

## 📂 Project Structure

```
railway-app/
│-- app.py           # Main Flask server
│-- .env             # Environment variables
│-- requirements.txt # Dependencies
│-- README.md        # Documentation
│-- static/          # Static files
│-- templates/       # HTML templates
```

---

## 🧾 Requirements

Add this in `requirements.txt`:

```txt
flask
pymongo
python-dotenv
qrcode
pillow
opencv-python
```

---

## 📌 Notes

* QR codes are expected to contain **serial IDs** stored in the database.
* The `/scan` endpoint will activate the **camera** and auto-detect QR codes.
* Once scanned, details can be **viewed or updated**.
* Database used: **MongoDB Atlas**.

