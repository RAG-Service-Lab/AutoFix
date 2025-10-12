
def make_filter(filter: dict):

    valid_items = {k: v for k, v in filter.items() if v != "None"}

    if valid_items:
        main_filter = valid_items.copy()
    else:
        main_filter = None
    sub_filter = {k: "None" for k in filter.keys()}

    return main_filter, sub_filter

def rerank(model, query, documents, k):
    if not documents:
        return []

    query_doc_pairs = [(query, doc.page_content) for doc in documents]
    
    scores = model.predict(query_doc_pairs)

    scored_docs = list(zip(documents, scores))
    scored_docs.sort(key=lambda x: x[1], reverse=True)
    reranked_docs = [doc[0] for doc in scored_docs[:k]]

    return reranked_docs

def retrieval(query,  main_vector_store, sub_vector_store, reranker=None):

    if main_vector_store is not None:
        main_docs = main_vector_store.similarity_search_with_relevance_scores(query, k=10, score_threshold=0.4)
        unique_main_docs = list({doc.page_content: doc for doc, score in main_docs}.values())
      
        if reranker:
            ranked_main_docs = rerank(reranker, query, unique_main_docs, k=3)
        else:
            ranked_main_docs = unique_main_docs
    else:
        ranked_main_docs = []

    sub_docs = sub_vector_store.similarity_search(query, k=10)
    unique_sub_docs = list({doc.page_content: doc for doc in sub_docs}.values())
    if reranker:
        ranked_sub_docs = rerank(reranker, query, unique_sub_docs, k=2)
    else:
        ranked_sub_docs = unique_sub_docs

    all_docs = ranked_main_docs + ranked_sub_docs

    context_text = '\n'.join([doc.page_content for doc in all_docs])

    return context_text