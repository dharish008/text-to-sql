import sys
from pathlib import Path

# Add project root directory to sys.path so modules like 'config' can be imported
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


import json
from collections import defaultdict, deque
from sqlalchemy import create_engine, inspect, text
from config import settings



def analyze_and_generate_whitelist(
    core_seeds: list[str] | None = None,
    max_hops: int = 2
) -> list[str]:
    """
    Inspects database relationships, filters operational noise,
    and walks foreign key graphs to identify the essential analytical tables.
    """
    engine = create_engine(settings.database_url)
    inspector = inspect(engine)
    dialect = engine.dialect.name

    all_tables = set(inspector.get_table_names())

    # 1. Identify and exclude system/vector tables
    system_patterns = {
        "langchain_pg_embedding",
        "langchain_pg_collection",
        "alembic_version",
        "flyway_schema_history"
    }

    # 2. Identify partition children (PostgreSQL specific)
    partition_children = set()
    if dialect == "postgresql":
        try:
            with engine.connect() as conn:
                res = conn.execute(text("""
                    SELECT c.relname 
                    FROM pg_inherits i 
                    JOIN pg_class c ON (i.inhrelid = c.oid);
                """))
                partition_children = {row[0] for row in res.fetchall()}
        except Exception:
            pass

    # Exclude technical/noise tables
    valid_tables = [
        t for t in all_tables 
        if t not in system_patterns 
        and t not in partition_children
        and not t.startswith("stg_")
        and not t.startswith("raw_")
    ]

    # 3. Build an undirected graph of foreign key relationships
    adjacency = defaultdict(set)
    table_row_counts = {}

    print(f"\nScanning {len(valid_tables)} tables for relationships and row counts...")

    with engine.connect() as conn:
        for table in valid_tables:
            # Estimate or count rows to help detect fact tables
            try:
                count_res = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                table_row_counts[table] = count_res.scalar() or 0
            except Exception:
                table_row_counts[table] = 0

            # Collect foreign keys
            fks = inspector.get_foreign_keys(table)
            for fk in fks:
                referred = fk.get("referred_table")
                if referred and referred in valid_tables:
                    adjacency[table].add(referred)
                    adjacency[referred].add(table)

    # 4. If no core seeds are provided, select top tables by row count/connectivity
    if not core_seeds:
        # Tables with high row counts and FK references are likely core fact tables
        sorted_by_size = sorted(
            valid_tables, 
            key=lambda t: (table_row_counts.get(t, 0), len(adjacency[t])), 
            reverse=True
        )
        core_seeds = sorted_by_size[:3]
        print(f"Auto-selected core transaction seed tables: {core_seeds}")
    else:
        print(f"Using defined core transaction seeds: {core_seeds}")

    # 5. Breadth-First Search (BFS) to gather joined entities within max_hops
    included = set(core_seeds)
    queue = deque([(seed, 0) for seed in core_seeds])

    while queue:
        current, depth = queue.popleft()
        if depth >= max_hops:
            continue

        for neighbor in adjacency[current]:
            if neighbor not in included:
                included.add(neighbor)
                queue.append((neighbor, depth + 1))

    # Add standalone reference/dimension tables that have reasonable size
    for table in valid_tables:
        if table not in included and 0 < table_row_counts.get(table, 0) < 5000:
            # Keep small lookup dictionaries/dimensions
            included.add(table)

    final_tables = sorted(list(included))
    return final_tables


if __name__ == "__main__":
    # You can pass specific starting fact tables, e.g., ["payment", "rental"]
    # or leave empty to let it auto-detect the hub tables
    whitelist = analyze_and_generate_whitelist(core_seeds=["payment", "rental"], max_hops=2)

    print("\n" + "=" * 50)
    print("RECOMMENDED TARGET_TABLES CONFIGURATION")
    print("=" * 50)
    print(f"\nAdd this line to your .env file:\n")
    print(f"TARGET_TABLES='{json.dumps(whitelist)}'")
    print("\nSelected tables:")
    for t in whitelist:
        print(f"  - {t}")