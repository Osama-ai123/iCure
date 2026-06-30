import faiss
import numpy as np
import pickle

# 1. حمّل الـ embeddings
embeddings = np.load('embeddings_250K.npy')
print(f"Loaded embeddings: {embeddings.shape}")

# 2. FAISS يحتاج float32
embeddings = embeddings.astype('float32')

# 3. ابنِ الـ index
# d = عدد الأرقام بكل vector (384)
d = embeddings.shape[1]
index = faiss.IndexFlatL2(d)

# 4. أضف الـ vectors للـ index
index.add(embeddings)
print(f"Total vectors in index: {index.ntotal}")

# 5. احفظ الـ index
faiss.write_index(index, 'faiss_index.bin')
print("Saved: faiss_index.bin")