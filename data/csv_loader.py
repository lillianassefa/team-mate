import pandas as pd
from typing import List, Dict, Any
from weaviate.weaviate_client import WeaviateClient
from weaviate.schema_manager import SchemaManager
from weaviate.http_client import HttpClient, HttpHandler
import os

from dotenv import load_dotenv
load_dotenv()

WEAVIATE_URL = os.getenv("WEAVIATE_URL")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")




schema_file_path = "/home/lillian/tenacious/team-mate/weaviate/schema.json"
async def load_csv_to_weaviate(csv_file: str):
    df = pd.read_csv(csv_file)

    
    http_client = HttpClient(WEAVIATE_URL, {"X-OpenAI-Api-Key": OPENAI_API_KEY})
    http_handler = HttpHandler(http_client)
    weaviate_client = WeaviateClient(http_handler)
    
    # Prepare data for Weaviate
    job_postings = []
    for _, row in df.iterrows():
        job_posting = {
            "title": row.get("title"),
            "company": row.get("company"),
            "company_link": row.get("company_link"),
            "place": row.get("place"),
            "date": row.get("date"),
            "apply_link": row.get("apply_link"),
            "post_link": row.get("post_link"),
            "seniority_level": row.get("seniority_level"),
            "employment_type": row.get("employment_type"),
            "description": row.get("description"),
            "job_title_id": row.get("job_title_id"),
            "job_desc_id": row.get("job_desc_id"),
        }
        job_postings.append(job_posting)

    
    success = await weaviate_client.batch_create_objects(job_postings, "JobPosting")
    print("created a batch job object on weaviate")
    if success:
        print("Successfully uploaded job postings to Weaviate.")
    else:
        print("Failed to upload job postings to Weaviate.")
