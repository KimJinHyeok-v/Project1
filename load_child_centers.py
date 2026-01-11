import json
import cx_Oracle

JSON_PATH = "data/child_centers_clean.json"

# 너 환경에 맞게 수정
USER = "child"
PW   = "child1234"
DSN  = cx_Oracle.makedsn("localhost", 1521, service_name="xe")

INSERT_SQL = """
INSERT INTO child_center
(district, center_name, address, phone, capacity, lat, lon, zipcode, fee, sat_yn)
VALUES
(:district, :center_name, :address, :phone, :capacity, :lat, :lon, :zipcode, :fee, :sat_yn)
"""

def is_nan(x):
    return isinstance(x, float) and (x != x)

def main():
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        rows = json.load(f)

    data = []
    for r in rows:
        data.append({
            "district": r.get("district"),
            "center_name": r.get("center_name"),
            "address": r.get("address"),
            "phone": r.get("phone"),
            "capacity": int(r["capacity"]) if r.get("capacity") is not None else None,
            "lat": None if is_nan(r.get("lat")) else r.get("lat"),
            "lon": None if is_nan(r.get("lon")) else r.get("lon"),
            "zipcode": (str(r.get("zipcode")).strip() if r.get("zipcode") is not None else None),
            "fee": int(r["fee"]) if r.get("fee") is not None else 0,
            "sat_yn": (r.get("sat_yn") or "N").strip().upper(),
        })

    conn = cx_Oracle.connect(USER, PW, DSN)
    cur = conn.cursor()
    cur.executemany(INSERT_SQL, data)
    conn.commit()

    print("Inserted rows:", cur.rowcount)

    cur.close()
    conn.close()

if __name__ == "__main__":
    main()
