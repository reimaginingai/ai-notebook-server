from retrieval_model import encode_sentence, get_encoding_similarities, get_cross_encoder_similarities
import torch
import pandas as pd


def eval_biencoder_model(truth_table):
    """
    Calculate model accuracy given a truth table of memos and corresponding queries.

    Args:
        truth_table (str): filepath to truth table csv in Answer,Question format.

    Returns:
        top1_accuracy (float): percent of the time the model's top choice is correct.
        top3_accuracy (float): percent of the time one of the model's top three choices is correct.
    """

    truth_table_db = pd.read_csv(truth_table)
    truth_table_db = truth_table_db.reset_index() # Make sure indexing works

    note_embeddings = []
    notes = []
    for index, row in truth_table_db.iterrows():
        note_embedding = encode_sentence(row['Answer'])
        note_embeddings.append(note_embedding)
        notes.append(row['Answer'])

    top3_incorrect = 0
    top1_incorrect = 0
    for index, row in truth_table_db.iterrows(): 
        question_embedding = encode_sentence(row['Question']) 
        similarities = get_encoding_similarities(question_embedding, note_embeddings)

        # Get the top 3 most similar answers
        top_k = 3
        top_values, top_indices = torch.topk(similarities, top_k)

        top_answers = [notes[i] for i in top_indices[0].tolist()]  # Retrieve top 3 answers

        # Check if the ground truth answer is among the top 3 answers
        if row['Answer'] not in top_answers:
            top3_incorrect += 1
            print("Query: ", row['Question'], "\n")
            print("Model responses: ", top_answers, "\n")
            print("Ground truth: ", row['Answer'], "\n\n")

        # Check if the ground truth answer is the model's top answer
        if row['Answer'] != top_answers[0]:
            top1_incorrect += 1

    total_queries = truth_table_db.shape[0]
    top3_accuracy = ((total_queries - top3_incorrect) / total_queries) * 100
    top1_accuracy = ((total_queries - top1_incorrect) / total_queries) * 100

    return top1_accuracy, top3_accuracy

# Uncomment to test biencoder by itself.
# top1_accuracy, top3_accuracy = eval_model('server/model/initial_training_data_notetaker.csv')
# print(f'% top choices correct: {top1_accuracy}')
# print(f'% correct answer in top 3 choices: {top3_accuracy}')


def eval_cross_encoder_model(truth_table):
    """
    Calculate cross encoder model accuracy given a truth table of memos and corresponding queries.

    For every wrong answer, prints out the query, the model's top three predictions, and the ground truth answer.

    Args:
        truth_table (str): filepath to truth table csv in Answer,Question format.

    Returns:
        top1_accuracy (float): percent of the time the model's top choice is correct.
        top3_accuracy (float): percent of the time one of the model's top three choices is correct.
    """

    truth_table_db = pd.read_csv(truth_table)
    truth_table_db = truth_table_db.reset_index() # Make sure indexing works

    # Turn Answer column of truth table into a list
    notes = truth_table_db['Answer'].tolist()

    top3_incorrect = 0
    top1_incorrect = 0
    for index, row in truth_table_db.iterrows():
        similarities = get_cross_encoder_similarities(row['Question'], notes)
        # Convert numpy array to tensor
        similarities = torch.from_numpy(similarities)

        # Get the top 3 most similar answers
        top_k = 3
        top_values, top_indices = torch.topk(similarities, top_k)

        top_answers = [notes[i] for i in top_indices.tolist()]  # Retrieve top 3 answers

        # Check if the ground truth answer is among the top 3 answers
        if row['Answer'] not in top_answers:
            top3_incorrect += 1


        # Check if the ground truth answer is the model's top answer
        if row['Answer'] != top_answers[0]:
            top1_incorrect += 1
            print("Query: ", row['Question'], "\n")
            print("Model responses: ", top_answers, "\n")
            print("Ground truth: ", row['Answer'], "\n\n")

    total_queries = truth_table_db.shape[0]
    top3_accuracy = ((total_queries - top3_incorrect) / total_queries) * 100
    top1_accuracy = ((total_queries - top1_incorrect) / total_queries) * 100

    return top1_accuracy, top3_accuracy

# Uncomment to test cross-encoder by itself.
top1_accuracy, top3_accuracy = eval_biencoder_model('server/model/initial_training_data_notetaker.csv')
print(f'% top choices correct: {top1_accuracy}')
print(f'% correct answer in top 3 choices: {top3_accuracy}')
