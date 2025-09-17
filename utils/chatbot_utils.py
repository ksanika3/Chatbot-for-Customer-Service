import os
import pandas as pd
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
import html

DATA_FILE = "data/faq_data.csv"
MODEL_NAME = "all-MiniLM-L6-v2"  # Small, fast, accurate

# Load model once
model = SentenceTransformer(MODEL_NAME)


def load_faq_data():
    """
    Load FAQ CSV.
    CSV must have 'question' and 'answer' columns.
    """
    if not os.path.exists(DATA_FILE):
        raise FileNotFoundError(f"{DATA_FILE} not found. Please create it.")
    
    data = pd.read_csv(DATA_FILE)
    if "question" not in data.columns or "answer" not in data.columns:
        raise ValueError("CSV must have 'question' and 'answer' columns")
    
    return data


def prepare_embeddings(data, save_index_path=None):
    """
    Create FAISS index from FAQ questions and return:
    - index (for searching)
    - question embeddings
    Optionally save FAISS index to disk.
    """
    questions = data["question"].str.lower().tolist()
    embeddings = model.encode(questions, convert_to_numpy=True, normalize_embeddings=True)

    dim = embeddings.shape[1]
    index = faiss.IndexFlatIP(dim)  # Cosine similarity if embeddings normalized
    index.add(embeddings.astype("float32"))

    if save_index_path:
        faiss.write_index(index, save_index_path)

    return index, embeddings


def load_faiss_index(index_path):
    """Load a saved FAISS index from disk"""
    if not os.path.exists(index_path):
        raise FileNotFoundError(f"{index_path} not found.")
    return faiss.read_index(index_path)


def get_response(user_input, data, index, threshold=0.6, top_k=3):
    """
    Search FAISS index for the closest FAQ answer(s)
    Returns the best answer and confidence score.
    """
    query_vec = model.encode(
        [user_input.lower()],
        convert_to_numpy=True,
        normalize_embeddings=True
    ).astype("float32")

    scores, indices = index.search(query_vec, top_k)

    # Prepare top-k results
    results = []
    for i, idx in enumerate(indices[0]):
        results.append({
            "question": data["question"].iloc[idx],
            "answer": data["answer"].iloc[idx],
            "score": float(scores[0][i])
        })

    best = results[0]

    # Low-confidence handling with suggestions
    if best["score"] < threshold:
        # If confidence low, provide suggestions
        suggestion_text = "\n".join([r["question"] for r in results[1:]]) if top_k > 1 else ""
        best["answer"] = (
            "I'm not sure about that. Did you mean:\n" + suggestion_text
            if suggestion_text else
            "I'm not sure about that. Could you rephrase or ask something else?"
        )

    return best["answer"], best["score"]
