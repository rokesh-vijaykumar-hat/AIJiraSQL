import os
import streamlit as st
import psycopg2
from dotenv import load_dotenv
import requests
import json

# Load environment variables
load_dotenv()

# Connect to PostgreSQL
def connect_db():
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD")
    )

# Get all tables excluding system schemas
def get_all_table_names(conn):
    with conn.cursor() as cur:
        cur.execute("""
            SELECT table_schema || '.' || table_name
            FROM information_schema.tables
            WHERE table_schema NOT IN ('pg_catalog', 'information_schema')
        """)
        return [row[0] for row in cur.fetchall()]

# Fetch schema for specific tables
def fetch_relevant_schema(conn, tables):
    schemas = {}
    for table in tables:
        schema_name, table_name = table.split('.')
        with conn.cursor() as cur:
            cur.execute("""
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_schema = %s AND table_name = %s
                ORDER BY ordinal_position
            """, (schema_name, table_name))
            schemas[table] = cur.fetchall()
    return schemas

# Get foreign key relationships
def fetch_foreign_keys(conn):
    with conn.cursor() as cur:
        cur.execute("""
            SELECT 
                tc.table_schema || '.' || tc.table_name,
                kcu.column_name,
                ccu.table_schema || '.' || ccu.table_name,
                ccu.column_name
            FROM information_schema.table_constraints AS tc
            JOIN information_schema.key_column_usage AS kcu
              ON tc.constraint_name = kcu.constraint_name
             AND tc.table_schema = kcu.table_schema
            JOIN information_schema.constraint_column_usage AS ccu
              ON ccu.constraint_name = tc.constraint_name
            WHERE tc.constraint_type = 'FOREIGN KEY'
        """)
        return cur.fetchall()

# Use LLM to rank tables by relevance
def llm_rank_tables_by_relevance(question, table_names, conn, top_k=5):
    table_schemas = {}
    with conn.cursor() as cur:
        for table in table_names:
            schema_name, table_name = table.split('.')
            cur.execute("""
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_schema = %s AND table_name = %s
                ORDER BY ordinal_position
                LIMIT 5
            """, (schema_name, table_name))
            table_schemas[table] = cur.fetchall()

    schema_info = ""
    for table, cols in table_schemas.items():
        schema_info += f"{table}:\n"
        for col, dtype in cols:
            schema_info += f"  - {col} ({dtype})\n"
        schema_info += "\n"

    prompt = f"""
You are a PostgreSQL assistant. Based on the user's question, rank the following tables by relevance, and return the most relevant {top_k} as a list.

### Tables and example columns:
{schema_info}

### Question:
{question}

### Output:
List only the top {top_k} fully qualified table names (e.g. schema.table), each on a new line.
"""

    output = call_ollama_stream(prompt)
    selected = []
    for line in output.strip().splitlines():
        cleaned = line.strip("`").split()[0]
        if cleaned in table_names:
            selected.append(cleaned)
    return selected[:top_k]

# Build prompt with full schema and relationships
def build_prompt_with_joins(question, schema_dict, fkeys):
    schema_str = ""
    for table, cols in schema_dict.items():
        schema_str += f"Table {table}:\n"
        for col, dtype in cols:
            schema_str += f"  - {col} ({dtype})\n"
        schema_str += "\n"

    if fkeys:
        schema_str += "### Foreign Key Relationships:\n"
        for fk in fkeys:
            schema_str += f"- {fk[0]}.{fk[1]} → {fk[2]}.{fk[3]}\n"

    return f"""You are an expert PostgreSQL assistant.
Given the following schema and relationships, generate the appropriate SQL query to answer the question.

### Schema:
{schema_str}

### Question:
{question}

### SQL:
"""

# LLM streaming call (Ollama)
def call_ollama_stream(prompt, model="gemma:2b"):
    response = requests.post(
        "http://ollama:11434/api/generate",
        json={"model": model, "prompt": prompt, "stream": True},
        stream=True,
        timeout=120
    )
    output = ""
    for line in response.iter_lines():
        if line:
            try:
                data = json.loads(line.decode("utf-8"))
                output += data.get("response", "")
            except json.JSONDecodeError:
                continue
    return output.strip()

# Streamlit UI
st.set_page_config(page_title="🧠 AI SQL Agent", layout="wide")
st.title("🧠 AI SQL Agent for PostgreSQL")

user_question = st.text_input("Ask a question about your database:")

if user_question:
    try:
        with connect_db() as conn:
            all_tables = get_all_table_names(conn)
            matched_tables = llm_rank_tables_by_relevance(user_question, all_tables, conn)
            schema = fetch_relevant_schema(conn, matched_tables)
            fkeys = fetch_foreign_keys(conn)
            prompt = build_prompt_with_joins(user_question, schema, fkeys)

        st.subheader("🔍 Prompt Sent to LLM")
        st.code(prompt, language="text")

        st.subheader("🧠 Generated SQL")
        sql_query = call_ollama_stream(prompt)
        st.code(sql_query, language="sql")

        with connect_db() as conn:
            with conn.cursor() as cur:
                try:
                    cur.execute(sql_query)
                    rows = cur.fetchall()
                    columns = [desc[0] for desc in cur.description]
                    if rows:
                        st.dataframe([dict(zip(columns, row)) for row in rows])
                    else:
                        st.info("✅ Query executed successfully but returned no results.")
                except Exception as exec_err:
                    st.error(f"⚠️ SQL Execution Error: {exec_err}")

    except Exception as e:
        st.error(f"❌ General Error: {e}")
