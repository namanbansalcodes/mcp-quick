import { App } from "@modelcontextprotocol/ext-apps";

// Initialize MCP App
const app = new App({ name: "Polymarket Market View", version: "1.0.0" });

// Connect to host
app.connect();

let marketData: any = null;

// Handle tool result from server
app.ontoolresult = (result) => {
  console.log("Received tool result:", result);

  try {
    const textContent = result.content?.find((c: any) => c.type === "text");
    if (textContent) {
      marketData = JSON.parse(textContent.text);
      renderMarket(marketData);
    }
  } catch (e) {
    console.error("Error parsing market data:", e);
    document.getElementById("app")!.innerHTML = `
      <div class="container">
        <div class="header">
          <h1>❌ Error Loading Market</h1>
          <div class="subtitle">${e instanceof Error ? e.message : "Unknown error"}</div>
        </div>
      </div>
    `;
  }
};

// Render the market UI
function renderMarket(data: any) {
  const appDiv = document.getElementById("app")!;

  const yesPct = Math.round(data.currentYes * 100);
  const noPct = Math.round(data.currentNo * 100);

  appDiv.innerHTML = `
    <div class="container">
      <div class="header">
        <h1>📊 ${data.title}</h1>
        <div class="subtitle">Live Polymarket Prediction</div>
      </div>

      <div class="stats">
        <div class="stat-card yes">
          <div class="label">Yes Price</div>
          <div class="value">${yesPct}¢</div>
        </div>

        <div class="stat-card no">
          <div class="label">No Price</div>
          <div class="value">${noPct}¢</div>
        </div>

        <div class="stat-card volume">
          <div class="label">Total Volume</div>
          <div class="value">${data.volume}</div>
        </div>
      </div>

      <div class="chart-container">
        <canvas id="marketChart"></canvas>
      </div>

      <div class="bet-controls">
        <h3 style="margin-bottom: 20px; color: #333;">📊 Place Your Bet</h3>

        <div class="bet-row">
          <div class="bet-card yes">
            <h4 style="color: #10b981;">✅ Bet YES</h4>
            <p>Current price: ${yesPct}¢</p>
            <input type="number" id="amount-yes" class="amount-input" placeholder="Amount ($)" value="10" min="1" />
            <button class="bet-btn yes" id="bet-yes-btn">
              Buy YES shares
            </button>
          </div>

          <div class="bet-card no">
            <h4 style="color: #ef4444;">❌ Bet NO</h4>
            <p>Current price: ${noPct}¢</p>
            <input type="number" id="amount-no" class="amount-input" placeholder="Amount ($)" value="10" min="1" />
            <button class="bet-btn no" id="bet-no-btn">
              Buy NO shares
            </button>
          </div>
        </div>

        <div id="result-message" class="result-message"></div>
      </div>
    </div>
  `;

  // Render chart
  renderChart(data);

  // Attach event listeners
  document.getElementById("bet-yes-btn")!.addEventListener("click", () => placeBet("YES"));
  document.getElementById("bet-no-btn")!.addEventListener("click", () => placeBet("NO"));
}

// Render chart using Canvas API (simple line chart)
function renderChart(data: any) {
  const canvas = document.getElementById("marketChart") as HTMLCanvasElement;
  if (!canvas) return;

  const ctx = canvas.getContext("2d")!;
  const width = canvas.parentElement!.clientWidth;
  const height = 300;

  canvas.width = width;
  canvas.height = height;

  const history = data.history || [];
  const labels = history.map((h: any) => h[0]);
  const yesData = history.map((h: any) => h[1] * 100);
  const noData = history.map((h: any) => h[2] * 100);

  // Simple chart rendering
  const padding = 40;
  const chartWidth = width - padding * 2;
  const chartHeight = height - padding * 2;

  // Clear canvas
  ctx.clearRect(0, 0, width, height);

  // Draw axes
  ctx.strokeStyle = "#e0e0e0";
  ctx.lineWidth = 2;
  ctx.beginPath();
  ctx.moveTo(padding, padding);
  ctx.lineTo(padding, height - padding);
  ctx.lineTo(width - padding, height - padding);
  ctx.stroke();

  // Draw YES line
  ctx.strokeStyle = "#10b981";
  ctx.lineWidth = 3;
  ctx.beginPath();
  yesData.forEach((val: number, i: number) => {
    const x = padding + (i / (yesData.length - 1)) * chartWidth;
    const y = height - padding - (val / 100) * chartHeight;
    if (i === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  });
  ctx.stroke();

  // Draw NO line
  ctx.strokeStyle = "#ef4444";
  ctx.lineWidth = 3;
  ctx.beginPath();
  noData.forEach((val: number, i: number) => {
    const x = padding + (i / (noData.length - 1)) * chartWidth;
    const y = height - padding - (val / 100) * chartHeight;
    if (i === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  });
  ctx.stroke();

  // Draw labels
  ctx.fillStyle = "#666";
  ctx.font = "12px sans-serif";
  ctx.textAlign = "center";
  labels.forEach((label: string, i: number) => {
    const x = padding + (i / (labels.length - 1)) * chartWidth;
    ctx.fillText(label.substring(5), x, height - padding + 20);
  });
}

// Place a bet by calling MCP server tool
async function placeBet(outcome: "YES" | "NO") {
  const amountInput = document.getElementById(
    outcome === "YES" ? "amount-yes" : "amount-no"
  ) as HTMLInputElement;
  const amount = parseFloat(amountInput.value) || 10;

  const resultDiv = document.getElementById("result-message")!;
  resultDiv.textContent = "Placing bet...";
  resultDiv.className = "result-message show";

  try {
    // Call MCP server tool
    const result = await app.callServerTool({
      name: "place_bet",
      arguments: {
        market_title: marketData.title,
        outcome: outcome,
        amount: amount,
      },
    });

    // Parse response
    const textContent = result.content?.find((c: any) => c.type === "text");
    if (textContent) {
      const response = JSON.parse(textContent.text);

      resultDiv.textContent = "✅ " + response.message;
      resultDiv.style.background = "#f0fdf4";
      resultDiv.style.borderColor = "#10b981";
      resultDiv.style.color = "#065f46";

      // Send message to Claude
      await app.sendMessage({
        role: "user",
        content: `I just placed a $${amount} bet on ${outcome} for "${marketData.title}"`,
      });
    }
  } catch (error) {
    console.error("Error placing bet:", error);
    resultDiv.textContent = "❌ Error: " + (error instanceof Error ? error.message : "Unknown error");
    resultDiv.style.background = "#fef2f2";
    resultDiv.style.borderColor = "#ef4444";
    resultDiv.style.color = "#991b1b";
  }
}

console.log("Polymarket MCP App initialized");
