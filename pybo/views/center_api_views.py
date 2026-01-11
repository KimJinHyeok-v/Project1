import math
import logging
from flask import Blueprint, request, jsonify
from sqlalchemy import create_engine, text
import config

logger = logging.getLogger(__name__)

bp = Blueprint("center_api", __name__, url_prefix="/api")
engine = create_engine(config.SQLALCHEMY_DATABASE_URI)


def _to_float(x):
    if x is None:
        return None
    try:
        return float(x)  # Decimal/NUMBER 대비
    except Exception:
        return None


def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2)
    return 2 * R * math.asin(math.sqrt(a))


def row_to_dict(m, distance_km=None):
    return {
        "center_id": m.get("center_id"),
        "district": m.get("district"),
        "center_name": m.get("center_name"),
        "address": m.get("address"),
        "phone": m.get("phone"),
        "zipcode": m.get("zipcode"),
        "fee": int(m.get("fee") or 0),
        "capacity": int(m.get("capacity")) if m.get("capacity") is not None else None,
        "lat": _to_float(m.get("lat")),
        "lon": _to_float(m.get("lon")),
        "sat_yn": m.get("sat_yn"),
        "distance_km": round(distance_km, 3) if distance_km is not None else None,
    }




@bp.get("/centers")
def list_centers():
    district = (request.args.get("district") or "").strip()
    sat_yn = (request.args.get("sat_yn") or "").strip().upper()
    limit = int(request.args.get("limit", 200))

    where = []
    params = {"limit": limit}

    if district:
        where.append("DISTRICT = :district")
        params["district"] = district

    if sat_yn in ("Y", "N"):
        where.append("SAT_YN = :sat_yn")
        params["sat_yn"] = sat_yn

    where_sql = "WHERE " + " AND ".join(where) if where else ""

    # Oracle 11g: LIMIT 대신 ROWNUM
    sql = text(f"""
    SELECT *
    FROM (
        SELECT
            CENTER_ID   AS center_id,
            DISTRICT    AS district,
            CENTER_NAME AS center_name,
            ADDRESS     AS address,
            PHONE       AS phone,
            ZIPCODE     AS zipcode,
            FEE         AS fee,
            CAPACITY    AS capacity,
            LAT         AS lat,
            LON         AS lon,
            SAT_YN      AS sat_yn
        FROM CHILD_CENTER
        {where_sql}
        ORDER BY DISTRICT, CENTER_NAME
    )
    WHERE ROWNUM <= :limit
""")


    with engine.connect() as conn:
        rows = conn.execute(sql, params).mappings().all()


    return jsonify([row_to_dict(r) for r in rows])

@bp.get("/centers/nearby")
def nearby_centers():
    lat = float(request.args["lat"])
    lon = float(request.args["lon"])

    radius_km = float(request.args.get("radius_km", 2))
    limit = int(request.args.get("limit", 20))
    district = (request.args.get("district") or "").strip()
    sat_yn = (request.args.get("sat_yn") or "").strip().upper()
    min_capacity = request.args.get("min_capacity")
    candidate_limit = int(request.args.get("candidate_limit", 1500))

    where = ["LAT IS NOT NULL", "LON IS NOT NULL"]
    params = {"candidate_limit": candidate_limit}

    if district:
        where.append("DISTRICT = :district")
        params["district"] = district

    if sat_yn in ("Y", "N"):
        where.append("SAT_YN = :sat_yn")
        params["sat_yn"] = sat_yn

    if min_capacity:
        where.append("CAPACITY >= :min_capacity")
        params["min_capacity"] = int(min_capacity)

    lat_delta = radius_km / 111.0
    lon_delta = radius_km / (111.0 * max(0.2, math.cos(math.radians(lat))))

    where.append("LAT BETWEEN :lat_min AND :lat_max")
    where.append("LON BETWEEN :lon_min AND :lon_max")
    params.update({
        "lat_min": lat - lat_delta,
        "lat_max": lat + lat_delta,
        "lon_min": lon - lon_delta,
        "lon_max": lon + lon_delta,
    })

    where_sql = "WHERE " + " AND ".join(where)

    sql = text(f"""
        SELECT *
        FROM (
            SELECT
                CENTER_ID   AS center_id,
                DISTRICT    AS district,
                CENTER_NAME AS center_name,
                ADDRESS     AS address,
                PHONE       AS phone,
                ZIPCODE     AS zipcode,
                FEE         AS fee,
                CAPACITY    AS capacity,
                LAT         AS lat,
                LON         AS lon,
                SAT_YN      AS sat_yn
            FROM CHILD_CENTER
            {where_sql}
        )
        WHERE ROWNUM <= :candidate_limit
    """)

    with engine.connect() as conn:
        rows = conn.execute(sql, params).mappings().all()

    result = []
    for r in rows:
        rlat = _to_float(r.get("lat"))
        rlon = _to_float(r.get("lon"))
        if rlat is None or rlon is None:
            continue

        d = haversine_km(lat, lon, rlat, rlon)
        if d <= radius_km:
            result.append((d, r))

    result.sort(key=lambda x: x[0])
    result = result[:limit]

    return jsonify([row_to_dict(r, distance_km=d) for d, r in result])
