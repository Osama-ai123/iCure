import numpy as np
import faiss
import pandas as pd
from sentence_transformers import SentenceTransformer
from google import genai
from dotenv import load_dotenv
import os
import time
import warnings
warnings.filterwarnings('ignore')
os.environ['HF_HUB_DISABLE_IMPLICIT_TOKEN'] = '1'
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# حمّل كل شي مرة وحدة
print("Loading model and index...")
embedding_model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
index = faiss.read_index(os.path.join(BASE_DIR, 'faiss_index.bin'))
df = pd.read_csv(os.path.join(BASE_DIR, 'ample_data_250K.csv'))
print("Ready!")

def search(question, top_k=5):
    question_vector = embedding_model.encode([question]).astype('float32')
    distances, indices = index.search(question_vector, top_k)
    results = []
    for i, idx in enumerate(indices[0]):
        results.append({
            'question': df.iloc[idx]['Question'],
            'answer': df.iloc[idx]['Answer'],
            'distance': float(distances[0][i])
        })
    return results

def ask(question, history=[], retries=3):
    
    # دايماً نطلب من Gemini يوضح ويوحّد المصطلحات
    history_text = ""
    if history:
        for msg in history:
            role = "User" if msg['role'] == 'user' else "Assistant"
            history_text += f"{role}: {msg['content']}\n"

    clarify_prompt = f"""Given this conversation (if any):
{history_text}
User's question: {question}

Rewrite the question as a standalone, clear medical question in English.
- Replace any foreign medical terms written in Arabic script with their proper English equivalents (e.g. "انيميا" → "anemia", "ديابيتس" → "diabetes")
- If there is conversation history, resolve any references like "it", "this", "them" based on context
- Return ONLY the rewritten question in English, nothing else."""

    for attempt in range(retries):
        try:
            search_question = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=clarify_prompt
            ).text.strip()
            break
        except:
            search_question = question

    # ابحث بالسؤال الواضح
    context_list = search(search_question)
    print(f"Search question: {search_question}")
    for i, r in enumerate(context_list):
        print(f"Result {i+1}: {r['question'][:80]}")

    context = ""
    for i, item in enumerate(context_list):
        context += f"{i+1}. Q: {item['question']}\n   A: {item['answer']}\n\n"

    history_text = ""
    if history:
        for msg in history:
            role = "User" if msg['role'] == 'user' else "Assistant"
            history_text += f"{role}: {msg['content']}\n"

    prompt = f"""You are iCure, an intelligent medical assistant.
Use ONLY the following medical information to answer the question.
If the answer is not in the provided context, say "I don't have enough information about this topic."
Always recommend consulting a doctor for medical decisions.
Provide a detailed, comprehensive answer based on the context. Do not give short or vague answers.
Answer in the same language as the question.
Write in plain text only. Do not use Markdown formatting, asterisks, hashes, or any special symbols.
When listing multiple items, write each item on its own line, numbered as "1." "2." "3." and so on. Keep each item concise and do not repeat information.

Medical Context:
{context}

Previous Conversation:
{history_text}

Question: {question}


Answer:"""

    for attempt in range(retries):
        try:
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt
            )
            return response.text
        except Exception as e:
            if attempt < retries - 1:
                print(f"Retrying... ({attempt + 1}/{retries})")
                time.sleep(5)
            else:
                return "Service temporarily unavailable. Please try again later."
# اختبار
if __name__ == "__main__":
    questions = [
        "What are the symptoms of diabetes?",
        "ما هي أعراض ارتفاع ضغط الدم؟"
    ]

    for q in questions:
        print(f"\nQ: {q}")
        print(f"A: {ask(q)}")
        print("-" * 50)