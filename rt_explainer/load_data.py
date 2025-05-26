# Standard library imports
import os

# Environment variable management
from dotenv import load_dotenv

# MongoDB-related imports
from pymongo import MongoClient

# LangChain imports
from langchain_openai import OpenAIEmbeddings
from langchain_mongodb import MongoDBAtlasVectorSearch
from langchain_mongodb.retrievers.hybrid_search import MongoDBAtlasHybridSearchRetriever

# Load environment variables
load_dotenv()

# MongoDB setup
def setup_mongo_client():
    """Initialize MongoDB client and return the collection."""
    client = MongoClient(os.getenv("MONGO_URL"))
    collection = client[os.getenv("MONGO_DB")][os.getenv("MONGO_COLLECTION")]

    # Print the number of documents in the collection
    num_documents = collection.count_documents({})
    print(f"Number of documents in the collection: {num_documents}")

    return collection

# Initialize vector store
def initialize_vector_store():
    """Initialize the MongoDB vector search and hybrid search retriever."""
    embeddings = OpenAIEmbeddings(openai_api_key=os.getenv("OPEN_API_KEY"))

    database_name = os.getenv("MONGO_DB")
    collection_name = os.getenv("MONGO_COLLECTION")
    namespace = f"{database_name}.{collection_name}"

    # Set up vector search
    vector_store = MongoDBAtlasVectorSearch.from_connection_string(
        connection_string=os.getenv("MONGO_URL"),
        embedding=embeddings,
        namespace=namespace,
        text_key="log_message",
        embedding_key="log_message_embedding",
        relevance_score_fn="dotProduct",
        vector_index="vector_index"
    )

    # Return hybrid search retriever
    return MongoDBAtlasHybridSearchRetriever(
        vectorstore=vector_store,
        search_index_name="search_index",
        top_k=3,
        fulltext_penalty=75,
        vector_penalty=25
    )

# Execute setup
collection = setup_mongo_client()
retriever = initialize_vector_store()
