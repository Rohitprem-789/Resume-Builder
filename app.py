from flask import Flask, render_template, request, jsonify
import pyodbc
import os
from openai import OpenAI
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    base_url="https://router.huggingface.co/v1",
    api_key=os.getenv("HF_TOKEN"),
)

app = Flask(__name__)

conn_str = (
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=DESKTOP-123ABC\\SQLEXPRESS;"
    "DATABASE=Portfolios;"
    "Trusted_Connection=yes;"
)

def build_fallback_summary(user_data):
    title = user_data.get("title", "")
    skills = user_data.get("skills", "")
    experience = user_data.get("experience", "")
    projects = user_data.get("projects", "")

    summary = "Motivated and enthusiastic candidate"

    if title:
        summary += f" with a strong interest in {title}"

    if skills:
        summary += f", skilled in {skills}"

    if experience:
        summary += f", with experience in {experience}"

    summary += "."

    if projects:
        summary += f" Demonstrates practical knowledge through projects such as {projects}."

    summary += " Passionate about continuous learning and eager to contribute effectively in a professional environment."

    return summary

@app.route("/")
def home():
    return render_template("portfolio_form.html")

@app.route("/generate_summary", methods=["POST"])
def generate_summary():
    try:
        data = request.get_json()
        user_data = data.get("data", {})

        if not user_data:
            return jsonify({"error": "No input data received"}), 400

        name = user_data.get("name", "")
        title = user_data.get("title", "")
        skills = user_data.get("skills", "")
        experience = user_data.get("experience", "")
        projects = user_data.get("projects", "")
        about = user_data.get("about", "")

        prompt = f"""
Write a professional resume summary for a candidate.

Candidate details:
Name: {name}
Title: {title}
Skills: {skills}
Experience: {experience}
Projects: {projects}
About: {about}

Requirements:
- Start with words like "Motivated", "Enthusiastic", "Detail-oriented", or "Driven"
- Do NOT use "I"
- Write in professional third-person resume style
- 3 to 4 lines only
- Make it ATS-friendly
- Do not include labels like Name, Skills, etc.
- Do not output bullet points or JSON
"""

        completion = client.chat.completions.create(
        model="meta-llama/Meta-Llama-3-8B-Instruct",
        messages=[
            {
                "role": "user",
            "content": prompt
            }
        ],
    )

        summary = completion.choices[0].message.content.strip()

        if summary:
            return jsonify({"summary": summary})

        fallback_summary = build_fallback_summary(user_data)
        return jsonify({"summary": fallback_summary})

    except Exception as e:
        print("HF error:", e)
        fallback_summary = build_fallback_summary(user_data)
        return jsonify({"summary": fallback_summary})
    

@app.route("/portfolio/<int:id>")
def view_portfolio(id):
    try:
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Portfolios WHERE PortfolioID = ?", id)
        row = cursor.fetchone()
        cursor.close()
        conn.close()

        if row:
            return render_template("portfolio_preview.html", portfolio=row)
        return "Portfolio not found", 404

    except Exception as e:
        return jsonify({"error": str(e)}), 500


def create_pdf_with_links():
    pdf_file = "portfolio.pdf"
    c = canvas.Canvas(pdf_file, pagesize=A4)

    c.setFont("Helvetica-Bold", 18)
    c.drawString(100, 800, "My Portfolio")

    c.setFont("Helvetica", 12)
    c.drawString(100, 760, "LinkedIn: Click Here")
    c.linkURL(
        "https://www.linkedin.com/in/your-linkedin-id",
        (100, 760, 250, 775),
        relative=0
    )

    c.drawString(100, 740, "GitHub: Click Here")
    c.linkURL(
        "https://github.com/your-github-id",
        (100, 740, 250, 755),
        relative=0
    )

    c.save()
    print(f"PDF saved: {pdf_file}")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)