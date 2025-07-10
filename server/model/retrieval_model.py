from sentence_transformers import SentenceTransformer, CrossEncoder
import numpy as np
import torch

# Choose sentence transformer (biencoder) model
biencoder_model = SentenceTransformer("all-mpnet-base-v2")
# Choose a cross-encoder model
cross_encoder_model = CrossEncoder('cross-encoder/ms-marco-MiniLM-L6-v2')

def encode_sentence(sentence):
    """
    Encodes a sentence based on a model definition

    Args:
        sentence (str): String containing the sentence to be encoded

    Returns:
        embedding (list): List containing embedding data
    """
    # Calculate embedding for sentence
    embedding = biencoder_model.encode([sentence]).tolist()  # Convert to list for Firebase compatibility

    return embedding


def get_encoding_similarities(question_embedding, note_embeddings):
    """
    Get the list of similarity scores given the question and note embeddings

    Args:
        question_embedding (list): List containing the question embedding data
        note_embeddings (list): List containing the note embedding data

    Returns:
        similarities (Tensor): List containing the similarity scores 
    """
    note_embeddings = np.array(note_embeddings, dtype=np.float32)
    note_embeddings = note_embeddings.reshape(note_embeddings.shape[0], -1)  # Reshape to (n, 768)

    
    # Calculate similarities
    similarities = biencoder_model.similarity(question_embedding, note_embeddings)
    
    
    return similarities

def get_cross_encoder_similarities(query, memos):
    """
    Run the cross encoder on a query and a set of memos, outputting a similarity to the query score for each memo.

    Args:
        query (str): The query to be compared with each memo.
        memos (list of str): Each memo to be compared with the query.

    Returns:
        (numpy.ndarray) The similarity to query score for each memo. (1 x num_memos)
    """
    scores = cross_encoder_model.predict([(query, memo) for memo in memos])
    return scores

def get_top_k_indices(similarities, k):
    # Get the top k most similar answers
    top_values, top_indices = torch.topk(similarities, k)
    return top_indices, top_values

        

