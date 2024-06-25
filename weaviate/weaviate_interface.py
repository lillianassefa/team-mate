from weaviate.schema_manager import SchemaManager
from weaviate.weaviate_client import WeaviateClient
from .http_client import HttpClient, HttpHandler
import pandas as pd


class WeaviateInterface:
    def __init__(self, url: str, openai_key: str, schema_file: str):
        self.http_handler = HttpHandler(HttpClient(url, {"X-OpenAI-Api-Key": openai_key}))
        self.client = WeaviateClient(self.http_handler)
        self.schema = SchemaManager(self.client, schema_file)

    async def async_init(self):
        """
        Asynchronous initialization tasks for WeaviateInterface.
        """
        if not await self.schema.is_valid():
            await self.schema.reset()

    # async def upload_csv_data(self, csv_file_path: str, class_name: str):
    #     """
    #     Uploads data from a CSV file to Weaviate.

    #     Parameters:
    #     csv_file_path (str): The path to the cleaned CSV file.
    #     class_name (str): The class name in Weaviate to upload the data to.
    #     """
    #     # Load the cleaned CSV file
    #     df_cleaned = pd.read_csv(csv_file_path)
        
    #     # Convert DataFrame to a list of dictionaries
    #     data_to_upload = df_cleaned.to_dict(orient='records')
        
    #     # Upload data to Weaviate in batches
    #     await self.client.batch_create_objects(data_to_upload, class_name)
