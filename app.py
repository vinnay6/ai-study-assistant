from flask import Flask, render_template, request, jsonify
import os
import pdfplumber
from groq import Groq
import json
from flask import session

# =========================
# GROQ API
# =========================

client = Groq(

    api_key=os.getenv("GROQ_API_KEY")

)
# =========================
# FLASK APP
# =========================

app = Flask(__name__)
app = Flask(__name__)

app.secret_key = "vinay_secret"

UPLOAD_FOLDER = "uploads"

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# =========================
# GLOBAL STORAGE
# =========================

pdf_context = ""

generated_mcqs = []

latest_ai_result = ""

# =========================
# AI SUMMARY FUNCTION
# =========================

def generate_ai_output(text):

    try:

        prompt = f"""
        You are an AI Study Assistant.

        Analyze the following study material and provide:

        1. Short Summary

        2. Important Key Points

        3. 5 Viva Questions

        Make the response beautiful and readable.

        Study Material:
        {text}
        """

        response = client.chat.completions.create(

            model="llama-3.1-8b-instant",

            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        return response.choices[0].message.content

    except Exception as e:

        return f"AI Error: {str(e)}"

# =========================
# MCQ GENERATION
# =========================

def generate_mcqs(text):

    global generated_mcqs

    prompt = f"""
    Generate 5 REAL multiple choice questions
    from the study material.

    Return ONLY valid JSON.

    Rules:

    - Each question must have 4 REAL options.
    - Do NOT use placeholders like:
      Option A, Option B etc.
    - Questions should be meaningful.
    - answer must be:
      "1", "2", "3", or "4"

    JSON Format:

    [
      {{
        "question":"What is Laplace Transform?",

        "options":[
          "A mathematical transform",
          "A programming language",
          "A database",
          "A network protocol"
        ],

        "answer":"1"
      }}
    ]

    Study Material:
    {text}
    """

    try:

        response = client.chat.completions.create(

            model="llama3-8b-8192",

            messages=[
                {
                    "role":"user",
                    "content":prompt
                }
            ]

        )

        response_text = response.choices[0].message.content

        # CLEAN JSON

        response_text = response_text.replace("```json", "")
        response_text = response_text.replace("```", "")

        generated_mcqs = json.loads(response_text)

        return generated_mcqs

    except Exception as e:

        print("MCQ Error:", e)

        session["mcqs"] = mcqs

        return []

# =========================
# HOME
# =========================

@app.route('/')
def home():

    return render_template("index.html")

# =========================
# DASHBOARD
# =========================

@app.route('/dashboard')
def dashboard():

    return render_template(

        "result.html",

        ai_result=latest_ai_result
    )

# =========================
# PDF UPLOAD
# =========================

@app.route('/upload', methods=['POST'])
def upload_file():

    global pdf_context
    global latest_ai_result

    file = request.files['pdf']

    if file.filename == "":

        return "No file selected"

    filepath = os.path.join(

        app.config['UPLOAD_FOLDER'],

        file.filename
    )

    file.save(filepath)

    extracted_text = ""

    with pdfplumber.open(filepath) as pdf:

        for page in pdf.pages:

            text = page.extract_text()

            if text:

                extracted_text += text

    # LIMIT TEXT

    extracted_text = extracted_text[:1000]

    pdf_context = extracted_text

    # AI SUMMARY

    ai_result = generate_ai_output(extracted_text)

    latest_ai_result = ai_result

    # GENERATE MCQS

    generate_mcqs(extracted_text)

    return render_template(

        "result.html",

        ai_result=ai_result
    )

# =========================
# TEST PAGE
# =========================

@app.route('/test')
def test():

    mcqs = session.get("mcqs", [])

    return render_template(
        "test.html",
        mcqs=mcqs
    )

# =========================
# SUBMIT TEST
# =========================

@app.route('/submit-test', methods=['POST'])
def submit_test():

    global generated_mcqs

    score = 0

    total = len(generated_mcqs)

    weak_topics = []

    correct_answers = []

    wrong_answers = []

    mcqs = session.get("mcqs", [])

    for i, mcq in enumerate(mcqs):

        user_answer = request.form.get(f"q{i+1}")

        correct_answer = mcq['answer']

        question = mcq['question']

        result_data = {

            "question": question,

            "correct": correct_answer,

            "user": user_answer
        }

        if (

            str(user_answer).strip()

            ==

            str(correct_answer).strip()

        ):

            score += 1

            correct_answers.append(result_data)

        else:

            wrong_answers.append(result_data)

            weak_topics.append(question)

    if total > 0:

        percentage = round((score / total) * 100)

    else:

        percentage = 0

    return render_template(

        "report.html",

        score=score,

        total=total,

        percentage=percentage,

        weak_topics=weak_topics,

        correct_answers=correct_answers,

        wrong_answers=wrong_answers
    )

# =========================
# AI CHAT
# =========================

@app.route('/chat', methods=['POST'])
def chat():

    global pdf_context

    data = request.get_json()

    user_message = data['message']

    prompt = f"""
    You are an AI Tutor.

    Answer ONLY from the study material below.

    Study Material:
    {pdf_context}

    Student Question:
    {user_message}
    """

    try:

        response = client.chat.completions.create(

            model="llama-3.1-8b-instant",

            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        answer = response.choices[0].message.content

        return jsonify({

            "reply": answer
        })

    except Exception as e:

        return jsonify({

            "reply": str(e)
        })

# =========================
# MAIN
# =========================

if __name__ == '__main__':

    app.run(host='0.0.0.0', port=5000)