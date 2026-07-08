import asyncio
import os
import json
from agents.generator import generate_article
from dotenv import load_dotenv

load_dotenv()

async def run_test():
    try:
        print("Starting manual generation test...")
        article = await generate_article("analisis")
        
        print("\n\n=== FINAL DB OBJECT ===")
        print(json.dumps(article, indent=2, ensure_ascii=False))
        print("=======================\n")
    except Exception as e:
        print(f"Generator test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    asyncio.run(run_test())
