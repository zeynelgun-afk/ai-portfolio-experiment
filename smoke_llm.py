"""Read-only real subscription smoke: no market fetch, no portfolio writes."""
import json
import llm_transport


def main():
    schema = {'name': 'local_smoke', 'schema': {'type': 'object',
              'properties': {'status': {'const': 'valid'}, 'paper_only': {'const': True}},
              'required': ['status', 'paper_only'], 'additionalProperties': False}}
    result = llm_transport.complete([{'role': 'user', 'content':
        'Return {"status":"valid","paper_only":true}. This is a transport test, not financial analysis.'}], schema)
    print(json.dumps({'provider': 'openai-codex', 'model': llm_transport.MODEL,
                      'validated': json.loads(result), 'paid_fallback': False}))


if __name__ == '__main__':
    main()
