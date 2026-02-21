"""
Standalone script to generate Bonn trees tileset files.

Usage:
    cd giessdenkiez-de-dwd-harvester/harvester
    source venv/bin/activate
    python generate_tileset.py

Output:
    temp/trees.csv           - All trees with radolan/watering data
    temp/trees-bonn.mbtiles  - tippecanoe vector tileset (upload to Mapbox Studio)
"""

import psycopg2
import subprocess
import os
import sys
from datetime import datetime
from tqdm import tqdm
from dotenv import load_dotenv

load_dotenv()

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "temp")
os.makedirs(OUTPUT_DIR, exist_ok=True)

TREES_CSV = os.path.join(OUTPUT_DIR, "trees.csv")
MBTILES = os.path.join(OUTPUT_DIR, "trees-bonn.mbtiles")


def connect_db():
    return psycopg2.connect(
        host=os.getenv("PG_SERVER", "localhost"),
        port=int(os.getenv("PG_PORT", 54322)),
        user=os.getenv("PG_USER", "postgres"),
        password=os.getenv("PG_PASS", "postgres"),
        dbname=os.getenv("PG_DB", "postgres"),
    )


def generate_csv(conn):
    current_year = datetime.now().year
    with conn.cursor() as cur:
        cur.execute("SET LOCAL statement_timeout = '10min';")
        cur.execute("""
            SELECT
                trees.id,
                ST_Y(geom) AS lat,
                ST_X(geom) AS lng,
                trees.radolan_sum,
                trees.pflanzjahr,
                COALESCE(SUM(w.amount), 0) AS watering_sum,
                CASE WHEN COUNT(ad.uuid) = 0 THEN FALSE ELSE TRUE END AS is_adopted_by_users,
                trees.bezirk AS district
            FROM trees
            LEFT JOIN trees_watered w ON w.tree_id = trees.id
                AND w.timestamp >= CURRENT_DATE - INTERVAL '30 days'
                AND DATE_TRUNC('day', w.timestamp) < CURRENT_DATE
            LEFT JOIN trees_adopted ad ON ad.tree_id = trees.id
            WHERE ST_CONTAINS(
                ST_SetSRID((SELECT ST_EXTENT(geometry) FROM radolan_geometry), 4326),
                trees.geom
            )
            GROUP BY trees.id, trees.lat, trees.lng, trees.radolan_sum,
                     trees.pflanzjahr, trees.bezirk;
        """)
        trees = cur.fetchall()

    print(f"Fetched {len(trees)} trees from DB")

    header = "id,lat,lng,radolan_sum,age,watering_sum,total_water_sum_liters,is_adopted_by_users,district"
    lines = []
    for tree in tqdm(trees, desc="Building CSV"):
        id, lat, lng = tree[0], tree[1], tree[2]
        radolan_sum = float(tree[3]) if tree[3] is not None else 0
        pflanzjahr = tree[4]
        age = "" if (pflanzjahr is None or pflanzjahr == 0) else int(current_year) - int(pflanzjahr)
        watering_sum = float(tree[5])
        total_water_sum_liters = (radolan_sum / 10.0) + watering_sum
        is_adopted_by_users = tree[6]
        district = tree[7]
        lines.append(f"{id}, {lat}, {lng}, {radolan_sum}, {age}, {watering_sum}, {total_water_sum_liters}, {is_adopted_by_users}, {district}")

    with open(TREES_CSV, "w") as f:
        f.write(header + "\n" + "\n".join(lines))
    print(f"Written: {TREES_CSV}")


def run_tippecanoe():
    print("Running tippecanoe...")
    result = subprocess.run(
        ["tippecanoe", "-zg", "-o", MBTILES, "--force", "--drop-fraction-as-needed", TREES_CSV],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print("tippecanoe stderr:", result.stderr)
        sys.exit(1)
    print(f"Written: {MBTILES}")


if __name__ == "__main__":
    print("Connecting to DB...")
    conn = connect_db()
    print("Generating trees.csv...")
    generate_csv(conn)
    conn.close()
    run_tippecanoe()
    print()
    print("Done! Next steps:")
    print(f"  1. Upload {MBTILES} to Mapbox Studio: https://studio.mapbox.com/tilesets/")
    print("  2. Tileset ID should be: giessdenkiez.bonn_trees")
    print("  3. Update VITE_MAPBOX_TREES_TILESET_URL in giessdenkiez-de/.env")
