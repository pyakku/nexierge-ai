from dotenv import load_dotenv
from openai import OpenAI
from time import perf_counter

load_dotenv()

client = OpenAI()

start = perf_counter()

response = client.responses.create(
    model="gpt-5-nano",
    input="What time is breakfast?"
)

print(response.output_text)
print(f"Time: {perf_counter() - start:.2f}s")