from crawl4ai import AsyncWebCrawler, AdaptiveCrawler
import asyncio
from crawl4ai import AdaptiveConfig

async def main():
    async with AsyncWebCrawler() as crawler:


        config = AdaptiveConfig(
            strategy="statistical",     # default -> exact terms
            confidence_threshold=0.8,    # Stop when 80% confident (default: 0.7)
            max_pages=30,               # Maximum pages to crawl (default: 20)
            top_k_links=5,              # Links to follow per page (default: 3)
            min_gain_threshold=0.05     # Minimum expected gain to continue (default: 0.1)
        )
        
        # # Configure embedding strategy -> semantic search
        # config = AdaptiveConfig(
        #     strategy="embedding",
        #     embedding_model="sentence-transformers/all-MiniLM-L6-v2",  # Default
        #     n_query_variations=10,  # Generate 10 query variations
        #     embedding_min_confidence_threshold=0.1  # Stop if completely irrelevant
        # )

        # # With custom embedding provider (e.g., OpenAI)
        # config = AdaptiveConfig(
        #     strategy="embedding",
        #     embedding_llm_config={
        #         'provider': 'openai/text-embedding-3-small',
        #         'api_token': 'your-api-key'
        #     }
        # )

        adaptive = AdaptiveCrawler(crawler, config)

        # Start crawling with a query
        result = await adaptive.digest(
            start_url="https://docs.python.org/3/",
            query="async context managers"
        )

        # View statistics
        # adaptive.print_stats(detailed=False)  # Summary table
        adaptive.print_stats(detailed=True)   # Detailed metrics
        
        # Check if query was irrelevant
        # if result.metrics.get('is_irrelevant', False):
        #     print("Query is unrelated to the content!")

        # Get the most relevant content
        relevant_pages = adaptive.get_relevant_content(top_k=5)
        for page in relevant_pages:
            print(f"- {page['url']} (score: {page['score']:.2f})")

if __name__ =="__main__":
    asyncio.run(main())
    
    
# config = AdaptiveConfig(
#     strategy="embedding",

#     # Model configuration
#     embedding_model="sentence-transformers/all-MiniLM-L6-v2",
#     embedding_llm_config=None,  # Use for API-based embeddings

#     # Query expansion
#     n_query_variations=10,  # Number of query variations to generate

#     # Coverage parameters
#     embedding_coverage_radius=0.2,  # Distance threshold for coverage
#     embedding_k_exp=3.0,  # Exponential decay factor (higher = stricter)

#     # Stopping criteria
#     embedding_min_relative_improvement=0.1,  # Min improvement to continue
#     embedding_validation_min_score=0.3,  # Min validation score
#     embedding_min_confidence_threshold=0.1,  # Below this = irrelevant

#     # Link selection
#     embedding_overlap_threshold=0.85,  # Similarity for deduplication

#     # Display confidence mapping
#     embedding_quality_min_confidence=0.7,  # Min displayed confidence
#     embedding_quality_max_confidence=0.95  # Max displayed confidence
# )
