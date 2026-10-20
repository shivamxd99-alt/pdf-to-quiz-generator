import streamlit as st
import pdfplumber
from docx import Document
import re
import random
from io import BytesIO

st.set_page_config(page_title="PDF / Document to Quiz Generator", page_icon="📝", layout="wide")

st.title("📝 Free PDF / Document to Quiz Generator")
st.markdown("Upload a PDF or Word document. The tool will analyze the text and generate quiz questions.")

def extract_text_from_pdf(file):
    text = ""
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text

def extract_text_from_docx(file):
    doc = Document(file)
    text = "\n".join([para.text for para in doc.paragraphs if para.text.strip()])
    return text

def clean_text(text):
    text = re.sub(r'\n+', '\n', text)
    text = re.sub(r' +', ' ', text)
    return text.strip()

def extract_key_sentences(text, max_sentences=15):
    sentences = re.split(r'(?<=[.!?])\s+', text)
    # Filter meaningful sentences
    key = []
    for s in sentences:
        s = s.strip()
        if 40 < len(s) < 300 and not s.startswith(('•', '-', '*')):
            key.append(s)
    # Prefer sentences with numbers or technical terms
    scored = sorted(key, key=lambda x: (len(re.findall(r'\d+', x)) + len(x.split())), reverse=True)
    return scored[:max_sentences]

def generate_questions(sentences, num_questions=10):
    questions = []
    used = set()
    
    for sent in sentences:
        if len(questions) >= num_questions:
            break
        if sent in used:
            continue
        used.add(sent)
        
        # True/False
        if random.random() > 0.4:
            questions.append({
                "type": "True / False",
                "question": sent,
                "answer": "True",
                "options": ["True", "False"]
            })
        else:
            # Fill in the blank (simple)
            words = sent.split()
            if len(words) > 8:
                # Try to blank a number or important word
                blank_idx = None
                for i, w in enumerate(words):
                    if re.search(r'\d', w) or (w[0].isupper() and len(w) > 3 and i > 2):
                        blank_idx = i
                        break
                if blank_idx is None:
                    blank_idx = len(words) // 2
                answer = words[blank_idx]
                words[blank_idx] = "______"
                questions.append({
                    "type": "Fill in the Blank",
                    "question": " ".join(words),
                    "answer": answer,
                    "options": []
                })
    
    # Add some MCQ style if possible
    return questions[:num_questions]

uploaded_file = st.file_uploader("Upload PDF or DOCX", type=["pdf", "docx"])

if uploaded_file:
    with st.spinner("Analyzing document..."):
        if uploaded_file.type == "application/pdf":
            raw_text = extract_text_from_pdf(uploaded_file)
        else:
            raw_text = extract_text_from_docx(uploaded_file)
        
        text = clean_text(raw_text)
        
        if len(text) < 100:
            st.error("Document has very little extractable text. Please upload a text-based PDF (not scanned image).")
        else:
            st.success(f"Extracted {len(text)} characters.")
            
            col1, col2 = st.columns([1, 1])
            with col1:
                num_q = st.slider("Number of questions", 5, 20, 10)
            with col2:
                q_type_pref = st.selectbox("Prefer question type", ["Mixed", "True/False", "Fill in the Blank"])
            
            if st.button("Generate Quiz", type="primary"):
                sentences = extract_key_sentences(text, max_sentences=30)
                questions = generate_questions(sentences, num_questions=num_q)
                
                if not questions:
                    st.warning("Could not generate questions. Try a document with clearer sentences.")
                else:
                    st.subheader("Generated Quiz Questions")
                    for i, q in enumerate(questions, 1):
                        with st.expander(f"Question {i} ({q['type']})"):
                            st.write(f"**Q:** {q['question']}")
                            if q['options']:
                                for opt in q['options']:
                                    st.write(f"- {opt}")
                            st.write(f"**Answer:** {q['answer']}")
                    
                    # Downloadable text
                    quiz_text = "PDF to Quiz Generator – Results\n" + "="*40 + "\n\n"
                    for i, q in enumerate(questions, 1):
                        quiz_text += f"{i}. [{q['type']}]\n{q['question']}\nAnswer: {q['answer']}\n\n"
                    
                    st.download_button(
                        "Download Quiz as Text",
                        data=quiz_text,
                        file_name="generated_quiz.txt",
                        mime="text/plain"
                    )
                    
                    st.info("Tip: For better AI-quality questions, copy the extracted text below and paste it into Grok / ChatGPT with the prompt: 'Create 10 MCQ and True/False questions from this text with answers.'")
                    
                    with st.expander("View Extracted Text"):
                        st.text_area("Text", text[:5000], height=300)

st.markdown("---")
st.caption("Note: This is a lightweight analyzer. For high-quality generative AI questions, combine the extracted text with a large language model.")
