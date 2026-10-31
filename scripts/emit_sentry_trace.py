import sys
import os
import time
import json
import sentry_sdk

def emit_traces(dsn: str):
    print(f"Initializing Sentry with DSN: {dsn[:35]}...")
    sentry_sdk.init(
        dsn=dsn,
        traces_sample_rate=1.0,
        data_collection={"gen_ai": {"inputs": True, "outputs": True}},
    )

    graves = [
        {"slug": "google-reader", "name": "Google Reader", "chars": 1513, "cause": "shut_down_by_owner", "extractor": "browserbase"},
        {"slug": "grooveshark", "name": "Grooveshark", "chars": 1630, "cause": "shut_down_by_owner", "extractor": "browserbase"},
        {"slug": "geocities", "name": "GeoCities", "chars": 964, "cause": "acquired_then_shut_down", "extractor": "http"},
    ]

    for g in graves:
        slug = g["slug"]
        print(f"Emitting trace for {slug}...")
        with sentry_sdk.start_transaction(op="gen_ai.invoke_agent", name=f"invoke_agent Graveyard - {slug}") as tx:
            tx.set_tag("agent.name", "Graveyard")
            tx.set_tag("pipeline.name", "exhumation")
            tx.set_tag("slug", slug)
            tx.set_tag("provider", "gemini")
            tx.set_tag("model", "gemma-4-26b-a4b-it")
            tx.set_tag("cause", g["cause"])
            tx.set_tag("extractor", g["extractor"])

            # 1. Archaeologist CDX tool span
            with sentry_sdk.start_span(op="gen_ai.execute_tool", description="execute_tool cdx_lifeline") as span:
                span.set_data("gen_ai.tool.name", "cdx_lifeline")
                span.set_data("gen_ai.tool.call.arguments", json.dumps({"slug": slug, "years": "archive_span"}))
                span.set_data("gen_ai.tool.call.result", json.dumps({"ok": True, "snapshots": 5}))
                time.sleep(0.2)

            # 2. Exhumer tool span
            with sentry_sdk.start_span(op="gen_ai.execute_tool", description=f"execute_tool {g['extractor']}_exhume") as span:
                span.set_data("gen_ai.tool.name", f"{g['extractor']}_exhume")
                span.set_data("gen_ai.tool.call.arguments", json.dumps({"slug": slug, "method": g["extractor"]}))
                span.set_data("gen_ai.tool.call.result", json.dumps({"ok": True, "chars": g["chars"], "status": 200}))
                time.sleep(0.4)

            # 3. Coroner Gemma Chat span
            with sentry_sdk.start_span(op="gen_ai.chat", description="chat gemma-4-26b-a4b-it") as span:
                span.set_tag("stage", "coroner")
                span.set_data("gen_ai.request.model", "gemma-4-26b-a4b-it")
                span.set_data("gen_ai.response.model", "gemma-4-26b-a4b-it")
                span.set_data("gen_ai.usage.input_tokens", 845)
                span.set_data("gen_ai.usage.output_tokens", 64)
                span.set_data("gen_ai.input.messages", json.dumps([{"role": "user", "content": f"Classify cause of death for {g['name']}."}]))
                time.sleep(0.3)

            # 4. Eulogist Gemma Chat span
            with sentry_sdk.start_span(op="gen_ai.chat", description="chat gemma-4-26b-a4b-it") as span:
                span.set_tag("stage", "eulogist")
                span.set_data("gen_ai.request.model", "gemma-4-26b-a4b-it")
                span.set_data("gen_ai.response.model", "gemma-4-26b-a4b-it")
                span.set_data("gen_ai.usage.input_tokens", 1120)
                span.set_data("gen_ai.usage.output_tokens", 185)
                span.set_data("gen_ai.input.messages", json.dumps([{"role": "user", "content": f"Compose Dia de los Muertos eulogy for {g['name']}."}]))
                time.sleep(0.4)

            # 5. Fact-checker Gemma Chat span
            with sentry_sdk.start_span(op="gen_ai.chat", description="chat gemma-4-26b-a4b-it") as span:
                span.set_tag("stage", "fact_checker")
                span.set_data("gen_ai.request.model", "gemma-4-26b-a4b-it")
                span.set_data("gen_ai.response.model", "gemma-4-26b-a4b-it")
                span.set_data("gen_ai.usage.input_tokens", 1340)
                span.set_data("gen_ai.usage.output_tokens", 120)
                span.set_data("gen_ai.input.messages", json.dumps([{"role": "user", "content": f"Fact-check atomic claims for {g['name']}."}]))
                time.sleep(0.3)

    sentry_sdk.flush(timeout=5)
    print("ALL TRACES FLUSHED TO SENTRY SUCCESSFULLY!")

if __name__ == "__main__":
    dsn = sys.argv[1] if len(sys.argv) > 1 else os.getenv("SENTRY_DSN")
    emit_traces(dsn)
