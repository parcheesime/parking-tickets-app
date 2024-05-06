from flask import Flask, jsonify, request, render_template
import requests
from collections import defaultdict

app = Flask(__name__, template_folder='templates')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/tickets')
def get_tickets():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    url = f'https://data.lacity.org/resource/4f5p-udkv.json?$where=issue_date between "{start_date}T00:00:00.000" and "{end_date}T00:00:00.000"'
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()

            # Initialize summary counters
            summary = defaultdict(int)

            for ticket in data:
                make = ticket.get('make', 'Unknown')
                color = ticket.get('color', 'Unknown')
                body_style = ticket.get('body_style', 'Unknown')

                # Update summary counts
                summary[(make, color, body_style)] += 1
            
            # Format summary data as list of dictionaries for JSON response
            summary_data = [{'make': make, 'color': color, 'body_style': body_style, 'count': count} 
                            for (make, color, body_style), count in summary.items()]

            total_fine_amount = sum(int(ticket['fine_amount']) for ticket in data if ticket.get('fine_amount', '').isdigit())
            for ticket in data:
                if 'loc_lat' not in ticket or 'loc_long' not in ticket:
                    ticket['loc_lat'] = '34.0522'  # Default latitude if missing
                    ticket['loc_long'] = '-118.2437'  # Default longitude if missing

            # Filter data based on date range
            filtered_data = [ticket for ticket in data if start_date <= ticket['issue_date'][:10] <= end_date]

            return jsonify({'tickets': filtered_data, 'summary': summary_data, 'total_fine_amount': total_fine_amount})
        else:
            return jsonify({'error': f'Failed to fetch data, status code {response.status_code}'}), response.status_code
    except requests.RequestException as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)

