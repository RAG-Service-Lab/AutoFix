
def make_filter(filter: dict):

    if any(list(filter.values())):
        main_filter = filter.copy()
    else:
        main_filter = None

    sub_filter = {k: {"$eq": "None"} for k in filter.keys()}

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

def retrieval(query, vector_store, filter, reranker=None):
    main_filter, sub_filter = make_filter(filter)

    if main_filter:
        main_docs = vector_store.similarity_search(query, k=10, filter=main_filter)
        unique_main_docs = list({doc.page_content: doc for doc in main_docs}.values())
        if reranker:
            ranked_main_docs = rerank(reranker, query, unique_main_docs, k=1)
        else:
            ranked_main_docs = unique_main_docs
    else:
        ranked_main_docs = []
    
    sub_docs = vector_store.similarity_search(query, k=10, filter=sub_filter)
    unique_sub_docs = list({doc.page_content: doc for doc in sub_docs}.values())
    if reranker:
        ranked_sub_docs = rerank(reranker, query, unique_sub_docs, k=1)
    else:
        ranked_sub_docs = unique_sub_docs

    print('검색된 문서: ')
    print(ranked_sub_docs)

    all_docs = ranked_main_docs + ranked_sub_docs

    context_text = '\n'.join([doc.page_content for doc in all_docs])

    return context_text