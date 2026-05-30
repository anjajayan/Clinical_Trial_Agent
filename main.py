import sys
import io
from MCP.clinical_research_server import call_ctg_api, call_pubmed_api
import asyncio 

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


async def main():
    print("Hello from clinical-trial-agent!")
    print(await call_pubmed_api("diabetes"))



if __name__ == "__main__":
    asyncio.run(main())
