"""
Polymarket MCP App - Shows live graphs of prediction markets
Quick POC to test MCP App display capabilities
"""

from fastmcp import FastMCP
import json
import urllib.request
import urllib.parse
from datetime import datetime, timedelta

mcp = FastMCP("Polymarket Live")


def fetch_markets(limit=10):
    """Fetch top markets from Polymarket API"""
    try:
        url = f"https://gamma-api.polymarket.com/markets?limit={limit}&closed=false"
        req = urllib.request.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0 (MCP App)')
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())
            return data
    except Exception as e:
        print(f"Error fetching markets: {e}")
        return []


def fetch_market_by_keyword(keyword):
    """Search for a market by keyword"""
    try:
        markets = fetch_markets(limit=50)
        keyword_lower = keyword.lower()
        for market in markets:
            question = market.get('question', '').lower()
            if keyword_lower in question:
                return market
        return None
    except Exception as e:
        print(f"Error searching markets: {e}")
        return None


@mcp.tool()
def place_bet(market_title: str, outcome: str, amount: float) -> str:
    """Simulate placing a bet on a market."""
    return json.dumps({
        "success": True,
        "market": market_title,
        "outcome": outcome,
        "amount": amount,
        "message": f"Placed ${amount:.2f} bet on '{outcome}' for market: {market_title}"
    })


@mcp.tool()
def view_market(keyword: str = "Trump") -> str:
    """View live betting graph for a Polymarket prediction. Search by keyword."""

    # Try to fetch real market data
    market_data = fetch_market_by_keyword(keyword)

    if market_data:
        # Extract real data from Polymarket API
        market_title = market_data.get('question', 'Unknown Market')

        # Parse JSON strings for outcomes and prices
        outcomes_str = market_data.get('outcomes', '["Yes", "No"]')
        prices_str = market_data.get('outcomePrices', '["0.5", "0.5"]')

        outcomes = json.loads(outcomes_str) if isinstance(outcomes_str, str) else outcomes_str
        outcome_prices = json.loads(prices_str) if isinstance(prices_str, str) else prices_str

        # Convert string prices to floats
        current_yes = float(outcome_prices[0]) if len(outcome_prices) > 0 else 0.5
        current_no = float(outcome_prices[1]) if len(outcome_prices) > 1 else 0.5

        # Format volume
        volume = market_data.get('volumeNum', market_data.get('volume', 0))
        if isinstance(volume, str):
            volume = float(volume)
        if volume > 1000000:
            volume_str = f"${volume / 1000000:.1f}M"
        elif volume > 1000:
            volume_str = f"${volume / 1000:.1f}K"
        else:
            volume_str = f"${volume:.0f}"

        # Generate mock history based on current price (real API doesn't provide history easily)
        # In production, you'd fetch from CLOB API /prices-history endpoint
        history = []
        base_date = datetime.now() - timedelta(days=30)
        for i in range(6):
            date = base_date + timedelta(days=i*5)
            # Simulate price evolution toward current price
            progress = i / 5
            yes_price = 0.5 + (current_yes - 0.5) * progress
            no_price = 1 - yes_price
            history.append([date.strftime("%Y-%m-%d"), yes_price, no_price])

        market = {
            "current_yes": current_yes,
            "current_no": current_no,
            "volume": volume_str,
            "history": history
        }
    else:
        # Fallback to mock data if API fails or market not found
        market_title = f"Market about '{keyword}' (mock data)"
        market = {
            "current_yes": 0.58,
            "current_no": 0.42,
            "volume": "$125M",
            "history": [
                ["2024-01-20", 0.45, 0.55],
                ["2024-01-25", 0.48, 0.52],
                ["2024-02-01", 0.52, 0.48],
                ["2024-02-10", 0.55, 0.45],
                ["2024-02-15", 0.56, 0.44],
                ["2024-02-20", 0.58, 0.42],
            ]
        }

    # Prepare data for Chart.js
    labels = [item[0] for item in market["history"]]
    yes_prices = [item[1] * 100 for item in market["history"]]  # Convert to percentage
    no_prices = [item[2] * 100 for item in market["history"]]

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Polymarket: {market_title}</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<script type="module">
  // Import MCP App SDK
  import {{ App }} from 'https://esm.sh/@modelcontextprotocol/ext-apps@0.1.0';

  const app = new App({{ name: "Polymarket", version: "1.0.0" }});
  app.connect();

  window.mcpApp = app;

  // Handle initial tool result
  app.ontoolresult = (result) => {{
    console.log('Received tool result:', result);
  }};
</script>
<style>
  * {{
    margin: 0;
    padding: 0;
    box-sizing: border-box;
  }}

  body {{
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    padding: 20px;
    min-height: 100vh;
  }}

  .container {{
    max-width: 900px;
    margin: 0 auto;
    background: white;
    border-radius: 16px;
    box-shadow: 0 20px 60px rgba(0,0,0,0.3);
    overflow: hidden;
  }}

  .header {{
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 30px;
  }}

  .header h1 {{
    font-size: 24px;
    margin-bottom: 10px;
    font-weight: 600;
  }}

  .header .subtitle {{
    opacity: 0.9;
    font-size: 14px;
  }}

  .stats {{
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 20px;
    padding: 30px;
    background: #f8f9fa;
    border-bottom: 1px solid #e0e0e0;
  }}

  .stat-card {{
    text-align: center;
    padding: 20px;
    background: white;
    border-radius: 12px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  }}

  .stat-card .label {{
    color: #666;
    font-size: 12px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 8px;
  }}

  .stat-card .value {{
    font-size: 32px;
    font-weight: 700;
    color: #333;
  }}

  .stat-card.yes .value {{
    color: #10b981;
  }}

  .stat-card.no .value {{
    color: #ef4444;
  }}

  .stat-card.volume .value {{
    color: #667eea;
    font-size: 24px;
  }}

  .chart-container {{
    padding: 30px;
    position: relative;
    height: 400px;
  }}

  .legend {{
    display: flex;
    justify-content: center;
    gap: 30px;
    padding: 0 30px 30px;
  }}

  .legend-item {{
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 14px;
  }}

  .legend-dot {{
    width: 12px;
    height: 12px;
    border-radius: 50%;
  }}

  .legend-dot.yes {{
    background: #10b981;
  }}

  .legend-dot.no {{
    background: #ef4444;
  }}

  .footer {{
    padding: 20px 30px;
    background: #f8f9fa;
    text-align: center;
    color: #666;
    font-size: 12px;
  }}

  .bet-controls {{
    padding: 30px;
    background: white;
    border-top: 1px solid #e0e0e0;
  }}

  .bet-row {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 20px;
    margin-bottom: 20px;
  }}

  .bet-card {{
    padding: 20px;
    border-radius: 12px;
    border: 2px solid #e0e0e0;
    transition: all 0.2s;
  }}

  .bet-card.yes {{
    border-color: #10b981;
    background: #f0fdf4;
  }}

  .bet-card.no {{
    border-color: #ef4444;
    background: #fef2f2;
  }}

  .bet-card:hover {{
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
  }}

  .bet-btn {{
    width: 100%;
    padding: 15px;
    font-size: 16px;
    font-weight: 600;
    border: none;
    border-radius: 8px;
    cursor: pointer;
    transition: all 0.2s;
    margin-top: 10px;
  }}

  .bet-btn.yes {{
    background: #10b981;
    color: white;
  }}

  .bet-btn.no {{
    background: #ef4444;
    color: white;
  }}

  .bet-btn:hover {{
    opacity: 0.9;
    transform: scale(1.02);
  }}

  .bet-btn:active {{
    transform: scale(0.98);
  }}

  .amount-input {{
    width: 100%;
    padding: 10px;
    font-size: 16px;
    border: 2px solid #e0e0e0;
    border-radius: 8px;
    margin-top: 10px;
  }}

  .result-message {{
    margin-top: 20px;
    padding: 15px;
    border-radius: 8px;
    background: #f0f9ff;
    border: 1px solid #0ea5e9;
    color: #0c4a6e;
    display: none;
  }}

  .result-message.show {{
    display: block;
    animation: fadeIn 0.3s;
  }}

  @keyframes fadeIn {{
    from {{ opacity: 0; transform: translateY(20px); }}
    to {{ opacity: 1; transform: translateY(0); }}
  }}

  .container {{
    animation: fadeIn 0.5s ease-out;
  }}
</style>
</head>
<body>

<div class="container">
  <div class="header">
    <h1>📊 {market_title}</h1>
    <div class="subtitle">Live Polymarket Prediction Graph</div>
  </div>

  <div class="stats">
    <div class="stat-card yes">
      <div class="label">Yes Price</div>
      <div class="value">{int(market['current_yes'] * 100)}¢</div>
    </div>

    <div class="stat-card no">
      <div class="label">No Price</div>
      <div class="value">{int(market['current_no'] * 100)}¢</div>
    </div>

    <div class="stat-card volume">
      <div class="label">Total Volume</div>
      <div class="value">{market['volume']}</div>
    </div>
  </div>

  <div class="chart-container">
    <canvas id="marketChart"></canvas>
  </div>

  <div class="legend">
    <div class="legend-item">
      <div class="legend-dot yes"></div>
      <span>YES price trend</span>
    </div>
    <div class="legend-item">
      <div class="legend-dot no"></div>
      <span>NO price trend</span>
    </div>
  </div>

  <div class="bet-controls">
    <h3 style="margin-bottom: 20px; color: #333;">📊 Place Your Bet</h3>

    <div class="bet-row">
      <div class="bet-card yes">
        <h4 style="color: #10b981; margin-bottom: 10px;">✅ Bet YES</h4>
        <p style="font-size: 14px; color: #666; margin-bottom: 10px;">
          Current price: {int(market['current_yes'] * 100)}¢
        </p>
        <input type="number" id="amount-yes" class="amount-input" placeholder="Amount ($)" value="10" min="1" />
        <button class="bet-btn yes" onclick="placeBet('YES')">
          Buy YES shares
        </button>
      </div>

      <div class="bet-card no">
        <h4 style="color: #ef4444; margin-bottom: 10px;">❌ Bet NO</h4>
        <p style="font-size: 14px; color: #666; margin-bottom: 10px;">
          Current price: {int(market['current_no'] * 100)}¢
        </p>
        <input type="number" id="amount-no" class="amount-input" placeholder="Amount ($)" value="10" min="1" />
        <button class="bet-btn no" onclick="placeBet('NO')">
          Buy NO shares
        </button>
      </div>
    </div>

    <div id="result-message" class="result-message"></div>
  </div>

  <div class="footer">
    Data updates every 5 minutes • Powered by Polymarket API
  </div>
</div>

<script>
  const ctx = document.getElementById('marketChart').getContext('2d');

  const chart = new Chart(ctx, {{
    type: 'line',
    data: {{
      labels: {json.dumps(labels)},
      datasets: [
        {{
          label: 'YES',
          data: {json.dumps(yes_prices)},
          borderColor: '#10b981',
          backgroundColor: 'rgba(16, 185, 129, 0.1)',
          borderWidth: 3,
          fill: true,
          tension: 0.4,
          pointRadius: 5,
          pointHoverRadius: 7,
          pointBackgroundColor: '#10b981',
          pointBorderColor: '#fff',
          pointBorderWidth: 2
        }},
        {{
          label: 'NO',
          data: {json.dumps(no_prices)},
          borderColor: '#ef4444',
          backgroundColor: 'rgba(239, 68, 68, 0.1)',
          borderWidth: 3,
          fill: true,
          tension: 0.4,
          pointRadius: 5,
          pointHoverRadius: 7,
          pointBackgroundColor: '#ef4444',
          pointBorderColor: '#fff',
          pointBorderWidth: 2
        }}
      ]
    }},
    options: {{
      responsive: true,
      maintainAspectRatio: false,
      plugins: {{
        legend: {{
          display: false
        }},
        tooltip: {{
          mode: 'index',
          intersect: false,
          backgroundColor: 'rgba(0, 0, 0, 0.8)',
          padding: 12,
          titleFont: {{ size: 14 }},
          bodyFont: {{ size: 13 }},
          callbacks: {{
            label: function(context) {{
              return context.dataset.label + ': ' + context.parsed.y.toFixed(1) + '¢';
            }}
          }}
        }}
      }},
      scales: {{
        y: {{
          beginAtZero: false,
          min: 0,
          max: 100,
          ticks: {{
            callback: function(value) {{
              return value + '¢';
            }},
            font: {{ size: 12 }}
          }},
          grid: {{
            color: 'rgba(0, 0, 0, 0.05)'
          }}
        }},
        x: {{
          ticks: {{
            font: {{ size: 11 }}
          }},
          grid: {{
            display: false
          }}
        }}
      }},
      interaction: {{
        mode: 'nearest',
        axis: 'x',
        intersect: false
      }}
    }}
  }});

  // Interactive betting function - calls MCP server tool
  window.placeBet = async function(outcome) {{
    const amountInput = outcome === 'YES' ?
      document.getElementById('amount-yes') :
      document.getElementById('amount-no');

    const amount = parseFloat(amountInput.value) || 10;
    const marketTitle = "{market_title}";

    // Show loading state
    const resultDiv = document.getElementById('result-message');
    resultDiv.textContent = 'Placing bet...';
    resultDiv.className = 'result-message show';

    try {{
      // Call MCP server tool
      const result = await window.mcpApp.callServerTool({{
        name: "place_bet",
        arguments: {{
          market_title: marketTitle,
          outcome: outcome,
          amount: amount
        }}
      }});

      // Parse result
      const response = JSON.parse(result.content[0].text);

      // Show success message
      resultDiv.textContent = '✅ ' + response.message;
      resultDiv.style.background = '#f0fdf4';
      resultDiv.style.borderColor = '#10b981';
      resultDiv.style.color = '#065f46';

      // Send message to Claude about the bet
      await window.mcpApp.sendMessage({{
        role: 'user',
        content: `I just placed a $$${{amount}} bet on ${{outcome}} for "${{marketTitle}}"`
      }});

    }} catch (error) {{
      console.error('Error placing bet:', error);
      resultDiv.textContent = '❌ Error: ' + error.message;
      resultDiv.style.background = '#fef2f2';
      resultDiv.style.borderColor = '#ef4444';
    }}
  }};

  // Simulate live updates (optional - for demo purposes)
  let updateCount = 0;
  setInterval(() => {{
    updateCount++;
    if (updateCount <= 3) {{
      // Add a new data point
      const lastYes = {yes_prices[-1]};
      const lastNo = {no_prices[-1]};

      // Small random fluctuation
      const newYes = lastYes + (Math.random() - 0.5) * 2;
      const newNo = 100 - newYes;

      chart.data.labels.push('Now +' + updateCount + 'm');
      chart.data.datasets[0].data.push(newYes);
      chart.data.datasets[1].data.push(newNo);
      chart.update();
    }}
  }}, 5000); // Update every 5 seconds for demo
</script>

</body>
</html>"""

    return html


@mcp.tool()
def list_trending_markets() -> str:
    """List the top trending Polymarket predictions."""

    markets = fetch_markets(limit=10)

    if not markets:
        return "Unable to fetch markets from Polymarket API."

    result = "🔥 Top Trending Polymarket Predictions:\n\n"

    for i, market in enumerate(markets, 1):
        question = market.get('question', 'Unknown')

        # Parse JSON strings
        prices_str = market.get('outcomePrices', '["0.5", "0.5"]')
        prices = json.loads(prices_str) if isinstance(prices_str, str) else prices_str

        volume = market.get('volumeNum', market.get('volume', 0))
        if isinstance(volume, str):
            volume = float(volume)

        if volume > 1000000:
            volume_str = f"${volume / 1000000:.1f}M"
        else:
            volume_str = f"${volume / 1000:.0f}K"

        yes_price = float(prices[0]) if len(prices) > 0 else 0.5
        yes_pct = int(yes_price * 100)

        result += f"{i}. {question}\n"
        result += f"   💹 YES: {yes_pct}¢ | 💰 Volume: {volume_str}\n\n"

    result += "\nUse view_market(keyword) to see detailed graph for any prediction!"

    return result


if __name__ == "__main__":
    mcp.run()
