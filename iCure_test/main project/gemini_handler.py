import google.generativeai as genai
from dotenv import load_dotenv
import os

# 1. حمّل الـ API key من ملف .env
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)

# 2. اختر الموديل
model = genai.GenerativeModel('gemini-2.5-flash')

def get_gemini_answer(question, context_list):
    """
    question: سؤال المستخدم
    context_list: قائمة النتائج من FAISS (أقرب 5 أسئلة وأجوبة)
    """
    
    # 3. ابنِ الـ context من نتائج FAISS
    context = ""
    for i, item in enumerate(context_list):
        context += f"{i+1}. Q: {item['question']}\n   A: {item['answer']}\n\n"
    
    # 4. البرومت — هذا قلب الـ RAG
    prompt = f"""You are iCure, an intelligent medical assistant.
Use ONLY the following medical information to answer the question.
If the answer is not in the provided context, say "I don't have enough information about this topic."
Always recommend consulting a doctor for medical decisions.
Answer in the same language as the question.

Medical Context:
{context}

Question: {question}

Answer:"""
    
    # 5. اطلب الجواب من Gemini
    response = model.generate_content(prompt)
    return response.text

# اختبار بسيط
if __name__ == "__main__":
    test_context = [
        {"question": "What are cold symptoms?", 
         "answer": "Cold symptoms include runny nose, sore throat, coughing, and mild fever."},
        {"question": "How to treat a cold?",
         "answer": "Rest, drink fluids, and take over-the-counter medications for symptoms."}
    ]
    
    result = get_gemini_answer("What are the symptoms of cold?", test_context)
    print(result)




