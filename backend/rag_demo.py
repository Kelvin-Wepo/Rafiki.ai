"""
RAG Demo Script

Interactive demonstration of the Kenyan Constitution RAG system.
This script shows how to query constitutional knowledge with citations.
"""

import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from backend.services.rag_service import get_rag_service, initialize_rag
from backend.config import get_settings

# Sample queries to test
SAMPLE_QUERIES = [
    "What are the fundamental rights and freedoms in the Kenyan Constitution?",
    "What does the constitution say about freedom of expression?",
    "What are the requirements for Kenyan citizenship?",
    "What are the powers and functions of the President?",
    "What does the constitution say about data protection and privacy?",
    "What are the devolved functions of county governments?",
    "What is the Bill of Rights?",
    "What does the constitution say about land ownership?",
]


def print_separator(char="=", length=80):
    """Print a separator line"""
    print(char * length)


def print_results(query: str, results, context: str, citations: list):
    """Pretty print query results"""
    print_separator()
    print(f"QUERY: {query}")
    print_separator()
    
    print(f"\nFound {len(results)} relevant sections:\n")
    
    for i, result in enumerate(results, 1):
        print(f"\n[Result {i}] (Relevance: {result.score:.2%})")
        print(f"Citation: {result.citation}")
        print(f"\nContent:")
        print(f"{result.content[:300]}..." if len(result.content) > 300 else result.content)
        print("-" * 80)
    
    if citations:
        print("\n📚 SOURCES:")
        for citation in citations:
            print(f"  {citation}")
    
    print_separator()


def main():
    """Main demo function"""
    print("\n" + "=" * 80)
    print("KENYAN CONSTITUTION RAG SYSTEM - DEMO")
    print("=" * 80)
    
    settings = get_settings()
    
    # Initialize RAG service
    print("\n🔧 Initializing RAG service...")
    rag = get_rag_service()
    
    # Check if database is initialized
    if not rag.is_initialized():
        print("\n⚠️  Database not initialized. Initializing now...")
        print("This may take a few minutes on first run...\n")
        
        try:
            result = initialize_rag(force_rebuild=False)
            print(f"\n✅ {result['message']}")
            print(f"   Total chunks indexed: {result['chunk_count']}")
        except FileNotFoundError:
            print("\n❌ ERROR: Constitution document not found!")
            print("   Please ensure the constitution PDF is at:")
            print(f"   {os.path.join(settings.BASE_DIR, 'backend/data/kenyan_constitution_2010.pdf')}")
            print("\n   You can download it from:")
            print("   https://www.mod.go.ke/wp-content/uploads/2018/10/CONSTITUTION-OF-KENYA-2010.pdf")
            return
        except Exception as e:
            print(f"\n❌ ERROR: Failed to initialize database: {e}")
            return
    else:
        print("✅ Database already initialized")
    
    # Get stats
    stats = rag.get_stats()
    print(f"\n📊 Database Statistics:")
    print(f"   Total chunks: {stats['total_chunks']}")
    print(f"   Chunk size: {stats['chunk_size']} characters")
    print(f"   Chunk overlap: {stats['chunk_overlap']} characters")
    print(f"   Top-K results: {stats['top_k']}")
    print(f"   Similarity threshold: {stats['similarity_threshold']}")
    
    # Interactive mode or sample queries
    print("\n" + "=" * 80)
    print("DEMO MODE")
    print("=" * 80)
    print("\nChoose an option:")
    print("1. Run sample queries")
    print("2. Interactive query mode")
    print("3. Exit")
    
    choice = input("\nEnter your choice (1-3): ").strip()
    
    if choice == "1":
        # Run sample queries
        print("\n🔍 Running sample queries...\n")
        
        for i, query in enumerate(SAMPLE_QUERIES, 1):
            print(f"\n{'='*80}")
            print(f"SAMPLE QUERY {i}/{len(SAMPLE_QUERIES)}")
            print(f"{'='*80}")
            
            results = rag.query(query, top_k=3)
            context, citations = rag.get_context_for_query(query, top_k=3)
            
            print_results(query, results, context, citations)
            
            if i < len(SAMPLE_QUERIES):
                input("\nPress Enter to continue to next query...")
    
    elif choice == "2":
        # Interactive mode
        print("\n🔍 Interactive Query Mode")
        print("=" * 80)
        print("Enter your questions about the Kenyan Constitution.")
        print("Type 'quit' or 'exit' to stop.\n")
        
        while True:
            query = input("\n❓ Your question: ").strip()
            
            if query.lower() in ['quit', 'exit', 'q']:
                print("\nGoodbye! 👋")
                break
            
            if not query:
                continue
            
            try:
                results = rag.query(query, top_k=5)
                context, citations = rag.get_context_for_query(query, top_k=5)
                
                if not results:
                    print("\n⚠️  No relevant results found. Try rephrasing your question.")
                else:
                    print_results(query, results, context, citations)
            
            except Exception as e:
                print(f"\n❌ Error: {e}")
    
    else:
        print("\nGoodbye! 👋")
    
    print("\n" + "=" * 80)
    print("Demo completed!")
    print("=" * 80)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user. Goodbye! 👋")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
