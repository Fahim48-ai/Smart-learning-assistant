import os
import PyPDF2
import google.generativeai as genai
from dotenv import load_dotenv
from flask import Flask, render_template, request, send_file

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
    global pdf_text
    global last_answer

    question = ""
    answer = ""

    if request.method == "POST":

        question = request.form["question"]

        try:

            prompt = f"""
You are a Smart Learning Assistant.

Use the uploaded PDF as the primary source.

PDF Content:
{pdf_text}

User Question:
{question}

Instructions:
- If the answer exists in the PDF, answer from the PDF.
- If it is not available in the PDF, answer using your general knowledge.
- Mention when the answer is from general knowledge.
"""

            response = model.generate_content(prompt)
            answer = response.text

        except Exception as e:
            answer = f"Error: {str(e)}"

        last_answer = answer

    return render_template("chat.html", question=question, answer=answer)


@app.route("/upload", methods=["GET", "POST"])
def upload():

    global pdf_text

    if request.method == "POST":

        file = request.files.get("pdf")

        if file and file.filename != "":

            os.makedirs("uploads", exist_ok=True)

            filename = os.path.join("uploads", file.filename)

            file.save(filename)

            text = ""

            with open(filename, "rb") as pdf_file:

                reader = PyPDF2.PdfReader(pdf_file)

                for page in reader.pages:
                    page_text = page.extract_text()

                    if page_text:
                        text += page_text + "\n"

            pdf_text = text

            try:
                os.remove(filename)
            except:
                pass

            return render_template("pdf_text.html", text=text)

    return render_template("upload.html")


@app.route("/search", methods=["POST"])
def search():

    global pdf_text

    word = request.form["word"]

    result = []

    for line in pdf_text.splitlines():

        if word.lower() in line.lower():
            result.append(line)

    return render_template("search.html", word=word, result=result)


@app.route("/download")
def download():

    global last_answer

    with open("answer.txt", "w", encoding="utf-8") as f:
        f.write(last_answer)

    return send_file("answer.txt", as_attachment=True)


if __name__ == "__main__":

    port = int(os.environ.get("PORT", 5000))

    app.run(host="0.0.0.0", port=port)