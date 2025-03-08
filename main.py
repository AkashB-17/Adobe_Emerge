# Import necessary libraries
import json
import requests
import time
import os

# API Key for Groq
api_key = " ** "

# Global variable to keep track of the total number of tokens
total_tokens = 0

# Function to load input file
def load_input_file(file_path):
    """
    Load input file which is a list of dictionaries.
    
    :param file_path: Path to the input file
    :return: List of dictionaries
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Input file not found: {file_path}")
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
        return data
    except json.JSONDecodeError:
        raise ValueError(f"Invalid JSON format in file: {file_path}")
    except Exception as e:
        raise Exception(f"Error loading file {file_path}: {str(e)}")

# Function to call the Groq API with rate limiting
def call_groq_api(api_key, model, messages, temperature=0.0, max_tokens=500, n=1):
    """
    Call the Groq API to get a response from the language model.
    """
    global total_tokens
    url = "https://api.groq.com/openai/v1/chat/completions"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    data = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "n": n,
        "stream": False
    }

    max_retries = 3
    retry_delay = 10  # Wait 10 seconds before retrying
    
    for attempt in range(max_retries):
        try:
            # Add delay between API calls
            time.sleep(2)  # Increased from 0.1 to 2 seconds
            
            response = requests.post(url, headers=headers, json=data, timeout=30)
            
            if response.status_code == 401:
                raise Exception("Invalid API key. Please check your API key.")
            elif response.status_code == 429:
                if attempt < max_retries - 1:
                    print(f"Rate limit hit. Waiting {retry_delay} seconds before retry {attempt + 1}/{max_retries}")
                    time.sleep(retry_delay)
                    continue
                raise Exception("Rate limit exceeded. Please wait before making more requests.")
            elif response.status_code != 200:
                raise Exception(f"API request failed with status code {response.status_code}")
                
            response_json = response.json()
            
            if 'choices' not in response_json or not response_json['choices']:
                raise Exception("Invalid response format from API")
                
            usage = response_json.get('usage', {})
            total_tokens += usage.get('completion_tokens', 0)
            
            return response_json, total_tokens
            
        except requests.exceptions.Timeout:
            if attempt < max_retries - 1:
                print(f"Request timed out. Retrying {attempt + 1}/{max_retries}")
                time.sleep(retry_delay)
                continue
            raise Exception("Request timed out after multiple attempts.")
        except requests.exceptions.RequestException as e:
            if attempt < max_retries - 1:
                print(f"Request failed. Retrying {attempt + 1}/{max_retries}")
                time.sleep(retry_delay)
                continue
            raise Exception(f"API request failed after multiple attempts: {str(e)}")
        except json.JSONDecodeError:
            raise Exception("Invalid JSON response from API")
        except Exception as e:
            raise Exception(f"Unexpected error: {str(e)}")
    
    raise Exception("Max retries exceeded")

# Function to generate SQL statements with rate limiting
def generate_sqls(data):
    """
    Generate SQL statements from the NL queries.
    
    :param data: List of NL queries
    :return: List of SQL statements
    """
    sql_statements = []
    
    for i, item in enumerate(data):
        nl_query = item.get('NL', '')
        if not nl_query:
            sql_statements.append({'NL': '', 'Query': ''})
            continue
            
        # Add delay between batches of queries
        if i > 0 and i % 5 == 0:
            print(f"Waiting 5 seconds after processing {i} queries...")
            time.sleep(5)
            
        # Prepare the prompt for SQL generation
        prompt = f"""Convert the following natural language query to SQL:
        Query: {nl_query}
        
        Generate only the SQL query without any explanation. The SQL should be compatible with PostgreSQL.
        """
        
        # Call Groq API with retries
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response, _ = call_groq_api(
                    api_key=api_key,
                    model="mixtral-8x7b-32768",
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a SQL expert. Convert natural language queries to SQL. Return only the SQL query without any explanation."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    temperature=0.1,
                    max_tokens=500
                )
                
                # Extract the SQL query from the response
                sql_query = response['choices'][0]['message']['content'].strip()
                
                # Clean up the SQL query
                if sql_query.startswith('sql'):
                    sql_query = sql_query[6:]
                if sql_query.endswith(''):
                    sql_query = sql_query[:-3]
                sql_query = sql_query.strip()
                
                sql_statements.append({
                    'NL': nl_query,
                    'Query': sql_query
                })
                break  # Exit retry loop on success
                
            except Exception as e:
                print(f"Error generating SQL for query: {nl_query} (Attempt {attempt + 1}/{max_retries})")
                print(f"Error: {str(e)}")
                if attempt == max_retries - 1:
                    sql_statements.append({
                        'NL': nl_query,
                        'Query': ''
                    })
                time.sleep(5)  # Wait before retrying
    
    return sql_statements

# Function to correct SQL statements with rate limiting
def correct_sqls(sql_statements):
    """
    Correct SQL statements if necessary.
    
    :param sql_statements: List of Dict with incorrect SQL statements and NL query
    :return: List of corrected SQL statements
    """
    corrected_sqls = []
    
    for item in sql_statements:
        nl_query = item.get('NL', '')
        incorrect_query = item.get('IncorrectQuery', '')
        
        if not nl_query or not incorrect_query:
            corrected_sqls.append({
                'NL': nl_query,
                'IncorrectQuery': incorrect_query,
                'CorrectQuery': ''
            })
            continue
            
        # Prepare the prompt for SQL correction
        prompt = f"""Given the following natural language query and incorrect SQL query, generate the correct SQL query:
        
        Natural Language Query: {nl_query}
        Incorrect SQL Query: {incorrect_query}
        
        Generate only the correct SQL query without any explanation. The SQL should be compatible with PostgreSQL.
        """
        
        # Log the prompt being sent to the API
        print("Sending API Request with Prompt:", prompt)
        
        # Call Groq API with retries
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response, _ = call_groq_api(
                    api_key=api_key,
                    model="mixtral-8x7b-32768",
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a SQL expert. Correct the given SQL query to match the natural language requirement. Return only the corrected SQL query without any explanation."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    temperature=0.1,
                    max_tokens=2048
                )
                
                # Log the API response
                print("API Response:", response)
                
                # Extract the corrected SQL query from the response
                correct_query = response['choices'][0]['message']['content'].strip()
                
                # Validate the corrected SQL query
                if not correct_query or not correct_query.startswith('SELECT'):
                    print(f"Invalid SQL query generated for: {nl_query}")
                    correct_query = ''  # Set to empty if invalid
                
                # Clean up the SQL query
                if correct_query.startswith('SELECT '):
                    correct_query = correct_query  # No need to remove 'SELECT '
                if correct_query.endswith(';'):
                    correct_query = correct_query[:-1]  # Remove trailing semicolon
                correct_query = correct_query.strip()
                
                # Log the results for debugging
                print(f"Correcting SQL for query: {nl_query}")
                print(f"Incorrect SQL: {incorrect_query}")
                print(f"Corrected SQL: {correct_query}")
                
                corrected_sqls.append({
                    'NL': nl_query,
                    'IncorrectQuery': incorrect_query,
                    'CorrectQuery': correct_query
                })
                break  # Exit retry loop on success
                
            except Exception as e:
                print(f"Error correcting SQL for query: {nl_query} (Attempt {attempt + 1}/{max_retries})")
                print(f"Error: {str(e)}")
                if attempt == max_retries - 1:
                    corrected_sqls.append({
                        'NL': nl_query,
                        'IncorrectQuery': incorrect_query,
                        'CorrectQuery': ''
                    })
                time.sleep(5)  # Wait before retrying
    
    return corrected_sqls

# Main function
def main():
    try:
        # Specify the paths to input files
        input_file_path_1 = 'train_generate_task.json'  # For SQL generation
        input_file_path_2 = 'train_query_correction_task.json'   # For SQL correction
        
        # Load data from input file
        data_1 = load_input_file(input_file_path_1)
        data_2 = load_input_file(input_file_path_2)
        
        print(f"Loaded {len(data_1)} queries for generation")
        print(f"Loaded {len(data_2)} queries for correction")
        
        start = time.time()
        # Generate SQL statements
        sql_statements = generate_sqls(data_1)
        generate_sqls_time = time.time() - start
        
        start = time.time()
        # Correct SQL statements
        corrected_sqls = correct_sqls(data_2)
        correct_sqls_time = time.time() - start
        
        assert len(data_2) == len(corrected_sqls) # If no answer, leave blank
        assert len(data_1) == len(sql_statements) # If no answer, leave blank
        
        # Save outputs to JSON files
        try:
            with open('output_sql_correction_task.json', 'w', encoding='utf-8') as f:
                json.dump(corrected_sqls, f, indent=2, ensure_ascii=False)
            print("Successfully saved correction output")
            
            with open('output_sql_generation_task.json', 'w', encoding='utf-8') as f:
                json.dump(sql_statements, f, indent=2, ensure_ascii=False)
            print("Successfully saved generation output")
        except Exception as e:
            print(f"Error saving output files: {str(e)}")
        
        return generate_sqls_time, correct_sqls_time
        
    except Exception as e:
        print(f"Error in main execution: {str(e)}")
        return 0, 0

if __name__ == "__main__":  # Fixed quotes
    try:
        generate_sqls_time, correct_sqls_time = main()
        print(f"Time taken to generate SQLs: {generate_sqls_time:.2f} seconds")
        print(f"Time taken to correct SQLs: {correct_sqls_time:.2f} seconds")
        print(f"Total tokens used: {total_tokens}")
    except Exception as e:
        print(f"Program execution failed: {str(e)}")
