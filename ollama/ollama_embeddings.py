import ollama
import time
import os
import json
import numpy as np
from numpy.linalg import norm

EMBED_MODEL_NAME = "mxbai-embed-large"
CHAT_MODEL_NAME = "phi3"

def parse_file(filename):
    with open(filename, encoding="utf-8-sig") as f:
        paragraphs = []
        buffer = []
        for line in f.readlines():
            line = line.strip()
            if line:
                buffer.append(line)
            elif len(buffer):
                paragraphs.append((' ').join(buffer))
                buffer  = []
        if len(buffer):
            paragraphs.append((' ').join(buffer))
    return paragraphs

def save_embeddings(filename, embeddings):
    # create the directory if it doesn not exists
    if not os.path.exists("embeddings"):
        os.mkdir("embeddings")
    
    # dump embeddings to json
    with open(f"embeddings\{filename}.json", 'w') as f:
        json.dump(embeddings, f)

def load_embeddings(filename):
    # check if the file exists
    if not os.path.exists(f"embeddings\{filename}.json"):
        return False
    
    # load embeddings from json
    with open(f"embeddings/{filename}.json", "r") as f:
        return json.load(f)

def get_embeddings(filename, modelname, chunks):
    # check if embeddings are already saved
    if (embeddings := load_embeddings(filename)) is not False:
        return embeddings
    # get embeddings from ollama
    embeddings = [
        ollama.embeddings(model=modelname, prompt=chunk)['embedding']
        for chunk in chunks
    ]

    # save embeddings
    save_embeddings(filename, embeddings)

    return embeddings

def find_most_similar(needle, haystack):
    needle_norm = norm(needle)
    similarity_scores = [
        np.dot(np.asarray(needle), item) / (needle_norm * norm(item)) for item in haystack
    ]

    return sorted(zip(similarity_scores, range(len(haystack))), reverse=True)

def main():
    SYSTEM_PROMPT = """You are a helpful reading assistant who answers questions 
        based on snippets of text provided in context. Answer only using the context provided, 
        being as concise as possible. If you're unsure, just say that you don't know.
        Context:
    """
    # open file
    filename = r"project_rag.txt"
    filepath = r"D:\Code\generative_ai\ollama\project_rag.txt"
    paragraphs = parse_file(filepath)
    
    embeddings = get_embeddings(filename, EMBED_MODEL_NAME, paragraphs)

    prompt = input("What do you want to know? -> ")
    prompt_embedding = ollama.embeddings(model=EMBED_MODEL_NAME, prompt=prompt)['embedding']

    # find most similar to each other
    most_similar_chunks = find_most_similar(prompt_embedding, embeddings)[:5]
    # for item in most_similar_chunks:
    #     print(item[0], paragraphs[item[1]])

    if most_similar_chunks:
        response = ollama.chat(
            model=CHAT_MODEL_NAME,
            messages=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT
                    + "\n".join(paragraphs[item[1]] for item in most_similar_chunks),
                },
                {
                    "role": "user",
                    "content": prompt
                },
            ]
        )
        print("\n\n")
        print(response["message"]["content"])
    else:
        print("Model could not find the answer from the context provided.")


if __name__ == "__main__":
    main()
