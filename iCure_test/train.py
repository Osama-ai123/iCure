import pandas as pd
from sentence_transformers import SentenceTransformer
import numpy as np
import torch

# 1. تأكد الـ GPU شغال
device = 'cuda' if torch.cuda.is_available() else 'cpu'
print(f"Using device: {device}")

# 2. حمّل الداتا وخذ عينة 50,000
df = pd.read_csv('clean_data.csv')
sample = df.sample(n=250000, random_state=52).reset_index(drop=True)
print(f"Sample size: {len(sample)}")

# 3. حمّل الموديل
# paraphrase-multilingual: يفهم العربي والإنجليزي بنفس الـ vector space
model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2', device=device)

# 4. ادمج السؤال والجواب معاً (أفضل من السؤال لوحده)
texts = (sample['Question'] + ' ' + sample['Answer']).tolist()

# 5. حوّل النصوص لـ vectors
# batch_size=64: كمية تُعالج مرة وحدة — إذا VRAM ضاقت نقللها
print("Generating embeddings...")
embeddings = model.encode(
    texts,
    batch_size=64,
    show_progress_bar=True,
    convert_to_numpy=True
)

print(f"Embeddings shape: {embeddings.shape}")
# المفروض تشوف: (50000, 384)
# 50000 سطر، كل سطر = 384 رقم يمثل معناه

# 6. احفظ الـ vectors والداتا
np.save('embeddings_250K.npy', embeddings)
sample.to_csv('ample_data_250K.csv', index=False)
print("Saved: embeddings.npy + sample_data.csv")

import numpy as np
embeddings = np.load('embeddings_250K.npy.npy')
print("Size in MB:", round(embeddings.nbytes / 1024 / 1024, 1))