from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates
import requests
from pydantic import BaseModel
from collections import defaultdict
from typing import List, Tuple

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
    try:
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

            total_row_count = sum(1 for ticket in data if ticket.get('fine_amount', '').isdigit())

            for ticket in data:
                ticket.setdefault('loc_lat', '34.0522')  # Default latitude
                ticket.setdefault('loc_long', '-118.2437')  # Default longitude

            filtered_data = [ticket for ticket in data if start_date <= ticket['issue_date'][:10] <= end_date]

            return {'tickets': filtered_data, 'summary': summary_data, 'total_fine_amount': total_row_count}
        else:
            raise HTTPException(status_code=response.status_code, detail="Failed to fetch data")
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
