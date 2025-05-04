```mermaid
sequenceDiagram
    participant User
    participant Streamlit
    participant LLMService
    participant LLMHandler
    participant MCPServer
    participant ProductHandler
    participant ProductAPI
    participant RatingAPI
    participant ProductsCSV
    participant RatingsCSV

    User->>Streamlit: Submit Query
    Streamlit->>LLMService: HTTP Request
    LLMService->>LLMHandler: Process Query
    LLMHandler->>LLMService: Extract Parameters
    LLMService->>MCPServer: HTTP Request
    MCPServer->>ProductHandler: Process Request
    ProductHandler->>ProductAPI: Query Products
    ProductAPI->>ProductsCSV: Read Data
    ProductsCSV-->>ProductAPI: Return Products
    ProductAPI-->>ProductHandler: Return Products
    ProductHandler-->>MCPServer: Return Products
    MCPServer->>RatingAPI: Get Ratings
    RatingAPI->>RatingsCSV: Read Ratings
    RatingsCSV-->>RatingAPI: Return Ratings
    RatingAPI-->>MCPServer: Return Ratings
    MCPServer-->>LLMService: Return Enriched Products
    LLMService-->>Streamlit: Return Results
    Streamlit-->>User: Display Results
```

# Sequence Flow

This diagram shows the detailed sequence of interactions between components when processing a user query, including the rating enrichment process. The MCP server directly calls the Rating API to enrich product data with ratings and receives the ratings in response. Both Product API and Rating API read their data from CSV files. 