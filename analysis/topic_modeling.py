from bertopic import BERTopic
from sklearn.decomposition import PCA

def run_topic_modeling(feedback_texts, n_topics=None):
    """
    feedback_texts: list of strings
    n_topics: set a number of topics or leave None for auto
    returns: topic_model, topics, probabilities
    """
    # Use PCA if dataset is small (<= 10 entries), else use default (UMAP)
    if len(feedback_texts) <= 10:
        # Use PCA to avoid UMAP errors on small datasets
        topic_model = BERTopic(language="english", nr_topics=n_topics, 
                              umap_model=PCA(n_components=min(len(feedback_texts), 2)))
    else:
        topic_model = BERTopic(language="english", nr_topics=n_topics)
    topics, probs = topic_model.fit_transform(feedback_texts)
    return topic_model, topics, probs
