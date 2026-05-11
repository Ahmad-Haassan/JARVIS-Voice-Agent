from duckduckgo_search import DDGS
import sys

def test_ddg_chat():
    try:
        print("Testing DuckDuckGo Chat...")
        with DDGS() as ddgs:
            response = ddgs.chat("How are you today?", model="gpt-4o-mini")
            print(f"SUCCESS: {response}")
            return True
    except Exception as e:
        print(f"FAILED: {e}")
        return False

if __name__ == "__main__":
    test_ddg_chat()
