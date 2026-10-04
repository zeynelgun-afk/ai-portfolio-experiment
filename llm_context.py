"""Model-facing research views; complete source records remain in saved artifacts."""
import copy


def research_view(data):
    result = copy.deepcopy(data)
    for symbol, row in result.items():
        if symbol.startswith('_') or not isinstance(row, dict):
            continue
        # Daily returns have already been reduced to the supplied return/indicator metrics.
        row.pop('daily_returns', None)
        analyst = row.get('analyst_revisions', {})
        if isinstance(analyst, dict):
            analyst.pop('quarantined_records', None)
            for window in analyst.get('windows', {}).values():
                if isinstance(window, dict):
                    window.pop('revisions', None)
        docs = row.get('source_documents', {})
        if isinstance(docs, dict):
            preferred = [citation.get('source_id')
                         for assessment in row.get('news_assessments', [])
                         for citation in assessment.get('citations', [])
                         if isinstance(citation, dict)]
            recent = sorted(docs, key=lambda key: str(docs[key].get('published_at', '')), reverse=True)
            selected = list(dict.fromkeys(key for key in preferred + recent if key in docs))[:8]
            row['source_documents'] = {key: docs[key] for key in selected}
            row['source_document_coverage'] = {'supplied': len(selected), 'available': len(docs)}
        # Keep provenance and explicitly mark excerpt coverage, rather than suggesting
        # that the model saw a complete article. Full text is retained on disk.
        for doc in row.get('source_documents', {}).values():
            if isinstance(doc, dict) and isinstance(doc.get('text'), str):
                if len(doc['text']) > 1800:
                    doc['text'] = doc['text'][:1800]
                    doc['text_truncated'] = True
    return result


def ledger_view(facts):
    # snapshot is an identical checksum on every fact, not research evidence.
    return {key: {field: value for field, value in fact.items() if field != 'snapshot'}
            for key, fact in facts.items()}
