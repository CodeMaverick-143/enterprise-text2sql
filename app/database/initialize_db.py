import os
import json
import sys
import sqlite3
from dotenv import load_dotenv

load_dotenv()

def parse_json_list(val):
    if not val:
        return []
    if isinstance(val, list):
        return val
    try:
        parsed = json.loads(val)
        if isinstance(parsed, list):
            return parsed
    except Exception:
        pass
    # Fallback parsing
    try:
        cleaned = val.strip().strip("[]()")
        if not cleaned:
            return []
        return [x.strip().strip('"\'') for x in cleaned.split(",")]
    except Exception:
        return []

def init_db(db_path: str = "./data/enterprise.db"):
    hf_token = os.getenv("HF_TOKEN")
    if hf_token:
        hf_token = hf_token.strip()
    
    if not hf_token:
        print("=" * 80, file=sys.stderr)
        print("ERROR: Hugging Face Access Token (HF_TOKEN) is not set in the environment or .env file.", file=sys.stderr)
        print("To run on the Beaver dataset, please:", file=sys.stderr)
        print("1. Log in to your Hugging Face account.", file=sys.stderr)
        print("2. Agree to the terms on the dataset pages:", file=sys.stderr)
        print("   - https://huggingface.co/datasets/beaverbench/beaver-table", file=sys.stderr)
        print("   - https://huggingface.co/datasets/beaverbench/beaver-query", file=sys.stderr)
        print("3. Create a token at https://huggingface.co/settings/tokens", file=sys.stderr)
        print("4. Set HF_TOKEN=your_token in the .env file.", file=sys.stderr)
        print("=" * 80, file=sys.stderr)
        sys.exit(1)
        
    split = os.getenv("BEAVER_SPLIT", "dw")
    target_db = os.getenv("BEAVER_DB_ID")
    
    # Lazy import datasets to avoid startup delay if missing
    try:
        from datasets import load_dataset
    except ImportError:
        print("ERROR: 'datasets' package is not installed. Please run 'uv sync' or install it.", file=sys.stderr)
        sys.exit(1)
        
    token_arg = None if hf_token == "use_env" else hf_token
    
    print(f"Loading beaverbench/beaver-table (split={split}) from Hugging Face...")
    try:
        table_dataset = load_dataset("beaverbench/beaver-table", split=split, token=token_arg)
    except Exception as e:
        print(f"Error loading beaverbench/beaver-table dataset: {e}", file=sys.stderr)
        print("Make sure you have requested access to beaverbench/beaver-table and provided a valid HF_TOKEN.", file=sys.stderr)
        sys.exit(1)
        
    if not target_db:
        # Auto-detect first database ID in the dataset
        target_db = table_dataset[0]["db"]
        print(f"No BEAVER_DB_ID specified. Auto-selected database: '{target_db}'")
        
    # Filter tables for the target database
    db_tables = [row for row in table_dataset if row["db"] == target_db]
    if not db_tables:
        available_dbs = sorted(list(set(row["db"] for row in table_dataset)))
        print(f"ERROR: Database '{target_db}' not found in split '{split}'.", file=sys.stderr)
        print(f"Available database IDs in split '{split}': {available_dbs}", file=sys.stderr)
        sys.exit(1)
        
    print(f"Found {len(db_tables)} tables for database '{target_db}'. Initializing SQLite database at '{db_path}'...")
    
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Drop all existing user tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
    existing_tables = [row[0] for row in cursor.fetchall()]
    for table in existing_tables:
        cursor.execute(f"DROP TABLE IF EXISTS \"{table}\"")
        
    # Enable foreign keys support in SQLite
    cursor.execute("PRAGMA foreign_keys = ON;")
    
    for row in db_tables:
        table_name = row["table_name"]
        column_names = parse_json_list(row["column_names"])
        column_types = parse_json_list(row["column_types"])
        
        if not column_names or not column_types:
            print(f"Warning: Empty columns for table '{table_name}', skipping.", file=sys.stderr)
            continue
            
        col_defs = []
        for col_name, col_type in zip(column_names, column_types):
            col_defs.append(f'"{col_name}" {col_type}')
            
        create_ddl = f"CREATE TABLE \"{table_name}\" (\n  " + ",\n  ".join(col_defs) + "\n);"
        
        try:
            cursor.execute(create_ddl)
            print(f"Created table: {table_name}")
        except Exception as e:
            print(f"Error creating table '{table_name}' with DDL:\n{create_ddl}\nError: {e}", file=sys.stderr)
            continue
            
        # Load and seed example rows
        example_rows = parse_json_list(row.get("example_rows"))
        if example_rows:
            inserted_count = 0
            for r in example_rows:
                try:
                    if isinstance(r, dict):
                        cols = list(r.keys())
                        vals = list(r.values())
                        placeholders = ",".join(["?"] * len(vals))
                        cols_str = ",".join([f'"{c}"' for c in cols])
                        cursor.execute(f"INSERT INTO \"{table_name}\" ({cols_str}) VALUES ({placeholders})", vals)
                        inserted_count += 1
                    elif isinstance(r, list):
                        placeholders = ",".join(["?"] * len(r))
                        # Only insert if dimensions match
                        if len(r) == len(column_names):
                            cols_str = ",".join([f'"{c}"' for c in column_names])
                            cursor.execute(f"INSERT INTO \"{table_name}\" ({cols_str}) VALUES ({placeholders})", r)
                            inserted_count += 1
                        else:
                            # Try to pad or truncate
                            padded_r = r[:len(column_names)] + [None] * max(0, len(column_names) - len(r))
                            cols_str = ",".join([f'"{c}"' for c in column_names])
                            cursor.execute(f"INSERT INTO \"{table_name}\" ({cols_str}) VALUES ({placeholders})", padded_r)
                            inserted_count += 1
                except Exception as ex:
                    # Ignore minor insertion errors (e.g. constraints)
                    pass
            print(f"  Seeded {inserted_count} rows into '{table_name}'.")
            
    conn.commit()
    conn.close()
    
    # Save active database metadata
    metadata = {
        "db_id": target_db,
        "split": split
    }
    metadata_path = "./data/active_db.json"
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)
        
    print(f"Database initialization complete for active DB '{target_db}'.")
    print(f"Active DB metadata saved to '{metadata_path}'.")

if __name__ == "__main__":
    init_db()
