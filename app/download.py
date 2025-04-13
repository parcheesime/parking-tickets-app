from fastapi import FastAPI, Request, HTTPException, Response
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
import requests
from pydantic import BaseModel
from collections import defaultdict
import csv
from io import StringIO

app = FastAPI()
templates = Jinja2Templates(directory='templates')

class TicketSummary(BaseModel):
    make: str
    color: str
    body_style: str
    count: int

@app.get("/")
async def read_root(request: Request):
    return templates.TemplateResponse("vue_map.html", {"request": request})

@app.get("/api/tickets", response_model=dict)
async def get_tickets(start_date: str, end_date: str):
    url = f'https://data.lacity.org/resource/4f5p-udkv.json?$where=issue_date between "{start_date}T00:00:00.000" and "{end_date}T00:00:00.000"'
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        summary = defaultdict(int)

        for ticket in data:
            make = ticket.get('make', 'Unknown')
            color = ticket.get('color', 'Unknown')
            body_style = ticket.get('body_style', 'Unknown')
            summary[(make, color, body_style)] += 1

        summary_data = [TicketSummary(make=make, color=color, body_style=body_style, count=count)
                        for (make, color, body_style), count in summary.items()]

        return {'tickets': data, 'summary': summary_data}
    else:
        raise HTTPException(status_code=response.status_code, detail="Failed to fetch data")

@app.get("/download-tickets")
async def download_tickets(start_date: str, end_date: str):
    url = f'https://data.lacity.org/resource/4f5p-udkv.json?$where=issue_date between "{start_date}T00:00:00.000" and "{end_date}T00:00:00.000"'
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        output = StringIO()
        writer = csv.writer(output)

        # Write the header
        writer.writerow(['Make', 'Color', 'Body Style', 'Count'])

        # Write the rows
        for ticket in data:
            writer.writerow([ticket['make'], ticket['color'], ticket['body_style'], ticket['count']])

        output.seek(0)
        return StreamingResponse(output, media_type="text/csv")

    else:
        raise HTTPException(status_code=response.status_code, detail="Failed to fetch data")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
