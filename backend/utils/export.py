from fastapi.responses import StreamingResponse
import io, csv

def to_csv_response(rows, filename="export.csv"):
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=list(rows[0].keys()) if rows else [])
    writer.writeheader()
    for r in rows:
        writer.writerow(r)
    output.seek(0)
    return StreamingResponse(iter([output.getvalue()]), media_type="text/csv", headers={
        "Content-Disposition": f"attachment; filename={filename}"
    })
