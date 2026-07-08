import PyPDF2
import os
import google.generativeai as genai
from flask import send_file
from dotenv import load_dotenv
from flask import Flask, render_template, request

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

model = genai.GenerativeModel("gemini-2.5-flash")

pdf_text = ""
last_answer = ""

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")

@app.route("/chat", methods=["GET", "POST"])
def chat():

    global last_answer
    global pdf_text

    question = ""
    answer = ""

    if request.method == "POST":
        question = request.form["question"]

        response = model.generate_content(
            f"""
You are a Smart Learning Assistant.

Use the uploaded PDF as the primary source.

PDF Content:
{pdf_text}

User Question:
{question}

Instructions:
- If the answer is available in the PDF, answer using the PDF.
- If the answer is NOT available in the PDF, answer using your general knowledge.
- Mention when the answer comes from general knowledge instead of the PDF.
"""
        )

        answer = response.text
        last_answer = answer

    return render_template("chat.html", question=question, answer=answer)

@app.route("/upload", methods=["GET", "POST"])
def upload():

    global pdf_text

    if request.method == "POST":

        file = request.files["pdf"]

        if file:
            filename = "uploads/" + file.filename
            file.save(filename)

            text = ""

            with open(filename, "rb") as pdf_file:
                reader = PyPDF2.PdfReader(pdf_file)

                for page in reader.pages:
                    text += page.extract_text() or ""
                pdf_text = text

            os.remove(filename)

            return render_template("pdf_text.html", text=text)

    return render_template("upload.html")

@app.route("/search", methods=["POST"])
def search():

    global pdf_text

    word = request.form["word"]

    lines = pdf_text.splitlines()

    result = []

    for line in lines:
        if word.lower() in line.lower():
            result.append(line)

    return render_template("search.html", word=word, result=result)

@app.route("/download")
def download():

    with open("answer.txt", "w", encoding="utf-8") as file:
        file.write(last_answer)

    return send_file("answer.txt", as_attachment=True)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)