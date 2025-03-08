# SQL Query Generation and Correction Tool

This tool uses the Groq API to generate SQL queries from natural language and correct existing SQL queries. It processes input files containing natural language queries and incorrect SQL queries, then generates corresponding correct SQL statements.

## Features

- Natural Language to SQL query generation
- SQL query correction
- Rate limiting and retry mechanisms
- Comprehensive error handling
- Progress tracking and timing statistics
- Token usage monitoring

## Prerequisites

- Python 3.6 or higher
- Groq API key
- Required Python packages:
  - requests
  - json
  - time
  - os

## Setup

1. Clone this repository
2. Install required packages:
   ```bash
   pip install requests
   ```
3. Set up your Groq API key in the `main.py` file:
   ```python
   api_key = "your_groq_api_key_here"
   ```

## Input Files

The tool expects two input JSON files:

1. `train_generate_task.json`: Contains natural language queries for SQL generation
   ```json
   [
     {
       "NL": "natural language query here"
     }
   ]
   ```

2. `train_query_correction_task.json`: Contains incorrect SQL queries for correction
   ```json
   [
     {
       "NL": "natural language query here",
       "IncorrectQuery": "incorrect SQL query here"
     }
   ]
   ```

## Usage

Run the script using:
```bash
python main.py
```

The script will:
1. Load input files
2. Generate SQL queries from natural language
3. Correct incorrect SQL queries
4. Save results to output files

## Output Files

The tool generates two output files:

1. `output_sql_generation_task.json`: Contains generated SQL queries
   ```json
   [
     {
       "NL": "original query",
       "Query": "generated SQL query"
     }
   ]
   ```

2. `output_sql_correction_task.json`: Contains corrected SQL queries
   ```json
   [
     {
       "NL": "original query",
       "IncorrectQuery": "original incorrect query",
       "CorrectQuery": "corrected SQL query"
     }
   ]
   ```

## Rate Limiting and Retries

The tool implements several rate limiting mechanisms:
- 2-second delay between API calls
- 5-second delay after every 5 queries
- 10-second retry delay on rate limit errors
- Maximum of 3 retries for failed requests

## Error Handling

The tool includes comprehensive error handling for:
- File not found errors
- Invalid JSON format
- API rate limits
- Network timeouts
- Invalid API responses
- SQL query validation

## Performance Monitoring

The tool tracks:
- Total processing time for generation and correction
- Total tokens used
- Number of queries processed
- Success/failure rates

## Example Usage

```python
# Input file (train_generate_task.json)
[
  {
    "NL": "Find all users who registered in the last month"
  }
]

# Output file (output_sql_generation_task.json)
[
  {
    "NL": "Find all users who registered in the last month",
    "Query": "SELECT * FROM users WHERE registration_date >= CURRENT_DATE - INTERVAL '1 month'"
  }
]
```

## Troubleshooting

Common issues and solutions:
1. API Key Issues
   - Verify your Groq API key is valid
   - Check for proper formatting in the code

2. Rate Limiting
   - The tool automatically handles rate limits with retries
   - Increase delay times if needed

3. File Not Found
   - Ensure input files exist in the correct directory
   - Check file permissions

4. Invalid JSON
   - Validate input JSON files
   - Check for proper formatting

## Contributing

Feel free to submit issues and enhancement requests!

## License

This project is licensed under the MIT License - see the LICENSE file for details. 