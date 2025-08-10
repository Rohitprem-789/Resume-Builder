from flask import Flask, render_template, request, jsonify
import pyodbc
import google.generativeai as genai

app = Flask(__name__)

# ✅ Configure Gemini API
genai.configure(api_key="AIzaSyBt6LZNEHH0TpCNfQOxK9m64JEmlFt9yqs")

# ✅ Database connection string
conn_str = (
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=DESKTOP-123ABC\\SQLEXPRESS;"
    "DATABASE=Portfolios;"
    "Trusted_Connection=yes;"
)

# ✅ AI Portfolio Summary Generation
@app.route("/generate_summary", methods=["POST"])
def generate_summary():
    try:
        user_data = request.json.get("data")
        model = genai.GenerativeModel("gemini-1.5-flash")

        prompt = f"Write a professional and concise portfolio summary for: {user_data}"

        response = model.generate_content(prompt)

        # ✅ Extract AI response text safely
        if hasattr(response, 'text') and response.text:
            summary = response.text
        elif hasattr(response, 'candidates') and response.candidates:
            summary = response.candidates[0].content.parts[0].text
        else:
            summary = "Sorry, I couldn't generate a summary."

        return jsonify({"summary": summary})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ✅ Homepage route
@app.route('/')
def home():
    return render_template('portfolio_form.html')


# ✅ Save portfolio to DB
@app.route('/save', methods=['POST'])
def save_portfolio():
    try:
        data = request.json
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO Portfolios (Name, Title, About, Skills, Experience, Projects, Email, Phone)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        data['name'], data['title'], data['about'],
        str(data['skills']), str(data['experience']), str(data['projects']),
        data['email'], data['phone'])

        conn.commit()
        conn.close()

        return jsonify({'message': 'Portfolio saved successfully!'})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ✅ View portfolio by ID
@app.route('/portfolio/<int:id>')
def view_portfolio(id):
    try:
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Portfolios WHERE PortfolioID = ?", id)
        row = cursor.fetchone()
        conn.close()

        if row:
            return render_template('portfolio_preview.html', portfolio=row)
        return "Portfolio not found", 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)
