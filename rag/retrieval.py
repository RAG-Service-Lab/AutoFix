
def make_filter(filter: dict):

    if any(list(filter.values())):
        main_filter = filter.copy()
    else:
        main_filter = None

    sub_filter = {k: {"$eq": "None"} for k in filter.keys()}

    return main_filter, sub_filter

def retrieval(query, vector_store, filter):
    main_filter, sub_filter = make_filter(filter)

    if main_filter:
        main_docs = vector_store.similarity_search(query, k=1, filter=main_filter)
        unique_main_docs = list({doc.page_content: doc for doc in main_docs}.values())
    else:
        unique_main_docs = []
    
    sub_docs = vector_store.similarity_search(query, k=1, filter=sub_filter)
    unique_sub_docs = list({doc.page_content: doc for doc in sub_docs}.values())
    all_docs = unique_main_docs + unique_sub_docs
    context_text = '\n'.join([doc.page_content for doc in all_docs])

    return context_text