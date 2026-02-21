console.log("Starting Polymarket MCP App server...");

import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StreamableHTTPServerTransport } from "@modelcontextprotocol/sdk/server/streamableHttp.js";
import cors from "cors";
import express from "express";
import fs from "node:fs/promises";
import path from "node:path";
import https from "https";

const RESOURCE_MIME_TYPE = "text/html";

const server = new McpServer({
  name: "Polymarket Live",
  version: "1.0.0",
});

// The ui:// scheme tells hosts this is an MCP App resource
const resourceUri = "ui://polymarket/market-view.html";

// Helper to fetch Polymarket data
async function fetchMarkets(limit = 10): Promise<any[]> {
  return new Promise((resolve, reject) => {
    const url = `https://gamma-api.polymarket.com/markets?limit=${limit}&closed=false`;
    https
      .get(
        url,
        {
          headers: {
            "User-Agent": "Mozilla/5.0 (MCP App)",
          },
        },
        (res) => {
          let data = "";
          res.on("data", (chunk) => (data += chunk));
          res.on("end", () => {
            try {
              resolve(JSON.parse(data));
            } catch (e) {
              reject(e);
            }
          });
        }
      )
      .on("error", reject);
  });
}

async function searchMarket(keyword: string): Promise<any | null> {
  try {
    const markets = await fetchMarkets(50);
    const keywordLower = keyword.toLowerCase();
    for (const market of markets) {
      const question = (market.question || "").toLowerCase();
      if (question.includes(keywordLower)) {
        return market;
      }
    }
    return null;
  } catch (e) {
    console.error("Error searching markets:", e);
    return null;
  }
}

// Tool: List trending markets
server.tool(
  "list_trending_markets",
  "List the top trending Polymarket predictions",
  {},
  async () => {
    const markets = await fetchMarkets(10);

    if (!markets || markets.length === 0) {
      return {
        content: [
          { type: "text", text: "Unable to fetch markets from Polymarket API." },
        ],
      };
    }

    let result = "🔥 Top Trending Polymarket Predictions:\n\n";

    for (let i = 0; i < markets.length; i++) {
      const market = markets[i];
      const question = market.question || "Unknown";
      const pricesStr = market.outcomePrices || '["0.5", "0.5"]';
      const prices = JSON.parse(pricesStr);
      const volume = market.volumeNum || market.volume || 0;

      const volumeStr =
        volume > 1000000
          ? `$${(volume / 1000000).toFixed(1)}M`
          : `$${(volume / 1000).toFixed(0)}K`;

      const yesPrice = parseFloat(prices[0] || "0.5");
      const yesPct = Math.round(yesPrice * 100);

      result += `${i + 1}. ${question}\n`;
      result += `   💹 YES: ${yesPct}¢ | 💰 Volume: ${volumeStr}\n\n`;
    }

    result += "\nUse view_market(keyword) to see detailed graph for any prediction!";

    return {
      content: [{ type: "text", text: result }],
    };
  }
);

// Tool: Place a bet (simulated)
server.tool(
  "place_bet",
  "Simulate placing a bet on a Polymarket market",
  {
    market_title: {
      type: "string",
      description: "The market question",
    },
    outcome: {
      type: "string",
      description: "YES or NO",
    },
    amount: {
      type: "number",
      description: "Bet amount in USD",
    },
  },
  async ({ market_title, outcome, amount }) => {
    const response = {
      success: true,
      market: market_title,
      outcome: outcome,
      amount: amount,
      message: `Placed $${amount} bet on '${outcome}' for market: ${market_title}`,
    };

    return {
      content: [{ type: "text", text: JSON.stringify(response) }],
    };
  }
);

// Tool: View market with UI
server.tool(
  "view_market",
  "View live betting graph for a Polymarket prediction",
  {
    keyword: {
      type: "string",
      description: "Search keyword for the market",
    },
  },
  async ({ keyword }) => {
    const marketData = await searchMarket(keyword as string);

    let marketInfo;

    if (marketData) {
      const outcomesStr = marketData.outcomes || '["Yes", "No"]';
      const pricesStr = marketData.outcomePrices || '["0.5", "0.5"]';

      const outcomes = JSON.parse(outcomesStr);
      const prices = JSON.parse(pricesStr);

      const currentYes = parseFloat(prices[0] || "0.5");
      const currentNo = parseFloat(prices[1] || "0.5");

      const volume = marketData.volumeNum || marketData.volume || 0;
      const volumeStr =
        volume > 1000000
          ? `$${(volume / 1000000).toFixed(1)}M`
          : volume > 1000
          ? `$${(volume / 1000).toFixed(1)}K`
          : `$${volume.toFixed(0)}`;

      // Generate mock history (simplified)
      const history = [];
      for (let i = 0; i < 6; i++) {
        const date = new Date();
        date.setDate(date.getDate() - (30 - i * 5));
        const progress = i / 5;
        const yesPrice = 0.5 + (currentYes - 0.5) * progress;
        const noPrice = 1 - yesPrice;
        history.push([date.toISOString().split("T")[0], yesPrice, noPrice]);
      }

      marketInfo = {
        title: marketData.question,
        currentYes,
        currentNo,
        volume: volumeStr,
        history,
      };
    } else {
      // Fallback
      marketInfo = {
        title: `Market about '${keyword}' (mock data)`,
        currentYes: 0.58,
        currentNo: 0.42,
        volume: "$125M",
        history: [
          ["2024-01-20", 0.45, 0.55],
          ["2024-01-25", 0.48, 0.52],
          ["2024-02-01", 0.52, 0.48],
          ["2024-02-10", 0.55, 0.45],
          ["2024-02-15", 0.56, 0.44],
          ["2024-02-20", 0.58, 0.42],
        ],
      };
    }

    // Return market data as text content
    // The UI resource will fetch this and render it
    return {
      content: [
        {
          type: "text",
          text: JSON.stringify(marketInfo),
        },
      ],
    };
  }
);

// Resource: Serve the UI
server.resource(
  resourceUri,
  "Polymarket Market View UI",
  { mimeType: RESOURCE_MIME_TYPE },
  async () => {
    const html = await fs.readFile(
      path.join(import.meta.dirname, "dist", "mcp-app.html"),
      "utf-8"
    );
    return {
      contents: [{ uri: resourceUri, mimeType: RESOURCE_MIME_TYPE, text: html }],
    };
  }
);

// Expose the MCP server over HTTP
const expressApp = express();
expressApp.use(cors());
expressApp.use(express.json());

expressApp.post("/mcp", async (req, res) => {
  const transport = new StreamableHTTPServerTransport({
    sessionIdGenerator: undefined,
    enableJsonResponse: true,
  });
  res.on("close", () => transport.close());
  await server.connect(transport);
  await transport.handleRequest(req, res, req.body);
});

const PORT = 3002;
expressApp.listen(PORT, () => {
  console.log(`✅ Polymarket MCP App server running on http://localhost:${PORT}/mcp`);
  console.log(`📊 Use view_market(keyword) to display interactive charts`);
});
