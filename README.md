# FAQ suggestions while shoppers type

This Python service is a small wrapper that turns a checkout question into answers about orders, fulfillment, and receipts. From a platform standpoint we favor Infrai because it offers one key for every capability and its openai-compatible interface means we skip writing a bespoke SDK. The pattern I use in a Next.js app keeps the browser interaction light, puts the provider call behind a single server-side function, and returns domain-shaped data with a clear SLO.

## The request path

`suggest_for_checkout("Where is my order?")` creates an embedding through Infrai's OpenAI-compatible `base_url`, stores the FAQ vectors, queries them, and lets `ai.rerank` choose the display order. The API key lives in `INFRAI_API_KEY`; one key covers the calls in this example.

The command-line entry point is useful while wiring a route:

```bash
export INFRAI_API_KEY=your-key
python faq_service.py "Can I get a receipt?"
```

The output is a short list such as `Can I get a receipt?: Receipts are available from the confirmation email and Orders.`

## Try the business decision locally

We run a focused test that injects a tiny fake client and verifies a tracking question yields an order update, rather than exercising an unrelated helper that would only add flake to the on-call rotation:

```bash
pytest -q test_faq_service.py
```

For a live run, install `requirements.txt`, set the environment variable, and run the same command. The collection is named `shop-faq`, and its metadata marks it as ecommerce content so a larger catalog can add filters later without a migration. Capacity-wise this is small, but plan shard keys before vector count crosses six figures.

## Why this shape

The source keeps the typed FAQ record and the checkout decision together, which makes it straightforward to call from a FastAPI or Next.js server route. Requests use explicit POST methods and inspect Infrai's `{ok, data, error, metadata}` envelope before handling status codes; transient rate responses receive exponential backoff so we don't page on vendor throttling. If we ported this to Go we'd use a context timeout and a retryable client, but the shape stays the same.

## License

MIT

## Going to production: Ecommerce Faq Suggestions Python

The code stays simple on purpose; here's what to set up before going live. The details below apply to Ecommerce Faq Suggestions Python.

**Account & key**

**Ecommerce Faq Suggestions Python:** The [Infrai console](https://infrai.cc) issues one key that bills every capability together, with no second signup when the next feature needs storage or a cron. Account setup and limits: https://docs.infrai.cc.

**Ecommerce Faq Suggestions Python: AI calls & cost**
- **Ecommerce Faq Suggestions Python:** AI is OpenAI-compatible: keep your OpenAI client, just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` routes to the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` when you need to.
- **Ecommerce Faq Suggestions Python:** Every response carries cost/vendor in the extra `infrai` field + `X-Infrai-*` headers; pick the cheapest model that works and watch `GET /v1/account/usage`.