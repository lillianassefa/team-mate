import pandas as pd
from datetime import datetime
from weaviate.weaviate_interface import *
import asyncio

async def load_csv_to_weaviate(csv_path: str, weaviate_client: WeaviateClient):
    df = pd.read_csv(csv_path)
    df['date_posted'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')  # Format the date
    
    classi = [
        {
          "class": "JobPosting",
          "description": "A job posting with details about the role and company.",
          "properties": [
            {
              "name": "title",
              "dataType": [
                "text"
              ],
              "description": "The job title"
            },
            {
              "name": "company",
              "dataType": [
                "text"
              ],
              "description": "The name of the company"
            },
            {
              "name": "company_link",
              "dataType": [
                "text"
              ],
              "description": "Link to the company's LinkedIn profile or website"
            },
            {
              "name": "location",
              "dataType": [
                "text"
              ],
              "description": "Location of the job"
            },
            {
              "name": "date_posted",
              "dataType": [
                "date"
              ],
              "description": "Date when the job was posted"
            },
            {
              "name": "apply_link",
              "dataType": [
                "text"
              ],
              "description": "Direct link to apply for the job"
            },
            {
              "name": "post_link",
              "dataType": [
                "text"
              ],
              "description": "Link to the job posting"
            },
            {
              "name": "seniority_level",
              "dataType": [
                "text"
              ],
              "description": "Seniority level of the job"
            },
            {
              "name": "employment_type",
              "dataType": [
                "text"
              ],
              "description": "Type of employment (e.g., Full-time, Part-time)"
            },
            {
              "name": "description",
              "dataType": [
                "text"
              ],
              "description": "Description of the job"
            }
          ]
        }
      ]
    
    await WeaviateClient.create_class(class_info=classi)
    print("Created class with")

    objects = []

    for _, row in df.iterrows():
        job_post = {
            "title": row['title'],
            "company": row['company'],
            "company_link": row['company_link'],
            "location": row['place'],
            "data": row["date"],
            "apply_link": row['apply_link'],
            "post_link": row['post_link'],
            "seniority_level": row['seniority_level'],
            "employment_type": row['employmnet_type'],
            "description": row['description']
        }
        objects.append(job_post)


    

    success = await WeaviateClient.batch_create_objects(objects, "JobPosting")
    if not success:
        print("Failed to load data into Weaviate")




async def main():
    csv_file_path = "cleaned_csvfile.csv"
    await load_csv_to_weaviate(csv_file_path)
    print("CSV data has been successfully imported to Weaviate.")

if __name__ == "__main__":
    asyncio.run(main())
