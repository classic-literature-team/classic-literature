import asyncio, traceback
from openai import AsyncOpenAI
from app.core.config import settings

LOG=open("_rawtool.out","w",encoding="utf-8",buffering=1)
def log(m): LOG.write(str(m)+"\n"); LOG.flush()

TOOL=[{
  "type":"function",
  "function":{
    "name":"add","description":"두 정수를 더한다",
    "parameters":{"type":"object","properties":{"a":{"type":"integer"},"b":{"type":"integer"}},"required":["a","b"]},
  },
}]

async def main():
    client=AsyncOpenAI(api_key=settings.openai_api_key, base_url=settings.openai_base_url or None, timeout=30)
    try:
        log("A) with tools non-stream...")
        r=await asyncio.wait_for(client.chat.completions.create(
            model=settings.openai_model,
            messages=[{"role":"user","content":"3 더하기 5를 add 도구로 계산해"}], tools=TOOL,
        ), timeout=40)
        log("A OK finish="+str(r.choices[0].finish_reason)+" tool_calls="+str(bool(r.choices[0].message.tool_calls)))
    except Exception as e:
        log("A "+type(e).__name__+": "+str(e))
    try:
        log("B) with tools STREAM...")
        stream=await client.chat.completions.create(
            model=settings.openai_model,
            messages=[{"role":"user","content":"3 더하기 5를 add 도구로 계산해"}], tools=TOOL, stream=True,
        )
        n=0
        async for chunk in stream:
            n+=1
            if n>=2: break
        log(f"B OK first_chunks n={n}")
    except Exception as e:
        log("B "+type(e).__name__+": "+str(e))
    log("END")
    LOG.close()

asyncio.run(main())
