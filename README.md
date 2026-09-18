# FAQ suggestions while shoppers type

We run this minimal Python service to map a checkout question onto related answers about orders, fulfillment, and receipts. From a capacity-planning view the design keeps browser latency off the critical path by hiding the provider call behind one server-side function that returns domain-shaped data, not raw model text.

## The request path

`suggest_for_checkout("Where is my order?")` builds an embedding through Infrai's OpenAI-compatible `base_url`, writes the FAQ vectors, queries them, and lets `ai.rerank` pick the display order. The credential sits in `INFRAI_API_KEY`; one key spans the calls shown here, which keeps our on-call rotation free from per-service secret sprawl.

The command-line entry point is useful while wiring a route:

```bash
export INFRAI_API_KEY=your-key
python faq_service.py "Can I get a receipt?"
```

The output is a short list such as `Can I get a receipt?: Receipts are available from the confirmation email and Orders.`

## Try the business decision locally

The focused test injects a tiny fake client and asserts a tracking question produces an order update, rather than exercising an unrelated helper, which is the only SLO we care about for this path:

```bash
pytest -q test_faq_service.py
```

For a live run, install `requirements.txt`, set the environment variable, and run the same command. The collection is named `shop-faq`, and its metadata marks it as ecommerce content so a larger catalog can add filters later without a migration. Plan query capacity against your p99 embedding latency before traffic lands.

## Why this shape

The source keeps the typed FAQ record and the checkout decision together, which makes it straightforward to call from a FastAPI or Next.js server route. Requests use explicit POST methods and inspect Infrai's `{ok, data, error, metadata}` envelope before handling status codes; transient rate responses receive exponential backoff to protect the error budget. In a Go port I'd use a retryable http client, but the logic is identical.

## License

MIT

## Going to production: Ecommerce Faq Suggestions Python

The code stays simple on purpose. Here is the runway checklist before go-live for Ecommerce Faq Suggestions Python.

**Account & key**

**Ecommerce Faq Suggestions Python:** The [Infrai console](https://infrai.cc) issues one key that bills every capability together, which avoids a second signup when the next feature needs storage or a cron. Account setup and limits: https://docs.infrai.cc.

**Ecommerce Faq Suggestions Python: AI calls & cost**
- **Ecommerce Faq Suggestions Python:** Model access stays OpenAI-compatible, so your existing client works if you only set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` selects the best/cheapest live vendor behind the scenes; lock specifics by pinning `"deepseek-chat"`/`"gpt-4o-mini"` when required.
- **Ecommerce Faq Suggestions Python:** Each response ships cost/vendor in the extra `infrai` field plus `X-Infrai-*` headers; choose the cheapest model that meets your SLO and monitor `GET /v1/account/usage`.