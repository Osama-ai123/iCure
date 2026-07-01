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
    
    # لو في history، نطلب من Gemini يوضح السؤال أولاً
    if history:
        history_text = ""
        for msg in history:
            role = "User" if msg['role'] == 'user' else "Assistant"
            history_text += f"{role}: {msg['content']}\n"
        
        clarify_prompt = f"""Given this conversation:
{history_text}
User's new question: {question}

Rewrite the user's question as a standalone, clear medical question.
Return ONLY the rewritten question, nothing else."""

        for attempt in range(retries):
            try:
                clarified = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=clarify_prompt
                ).text.strip()
                break
            except:
                clarified = question
        
        search_question = clarified
    else:
        search_question = question

    # ابحث بالسؤال الواضح
    context_list = search(search_question)

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
Answer in the same language as the question.

Medical Context:
{context}

Previous Conversation:
{history_text}

Question: {question}

search_question = clarified
print(f"Clarified question: {search_question}")  # أضف هذا

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