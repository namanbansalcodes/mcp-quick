import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
  ListResourcesRequestSchema,
  ReadResourceRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import https from "https";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Log to stderr only (stdout is for MCP protocol)
const log = (msg: string) => console.error(msg);

// MCP App resource MIME type
const RESOURCE_MIME_TYPE = "text/html;profile=mcp-app";

const server = new Server(
  {
    name: "polymarket-app",
    version: "1.0.0",
  },
  {
    capabilities: {
      tools: {},
      resources: {},
    },
  }
);

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
    log(`Error searching markets: ${e}`);
    return null;
  }
}

// List tools
server.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: [
      {
        name: "view_market",
        description: "View live betting graph for a Polymarket prediction",
        inputSchema: {
          type: "object",
          properties: {
            keyword: {
              type: "string",
              description: "Search keyword for the market",
            },
          },
          required: ["keyword"],
        },
        _meta: {
          ui: {
            resourceUri: resourceUri,
          },
        },
      },
    ],
  };
});

// Call tool
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  if (request.params.name === "view_market") {
    const keyword = (request.params.arguments?.keyword as string) || "Trump";
    const marketData = await searchMarket(keyword);

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

    return {
      content: [
        {
          type: "text",
          text: JSON.stringify(marketInfo),
        },
      ],
    };
  }

  throw new Error(`Unknown tool: ${request.params.name}`);
});

// List resources
server.setRequestHandler(ListResourcesRequestSchema, async () => {
  return {
    resources: [
      {
        uri: resourceUri,
        name: "Polymarket Market View",
        mimeType: RESOURCE_MIME_TYPE,
      },
    ],
  };
});

// Read resource
server.setRequestHandler(ReadResourceRequestSchema, async (request) => {
  if (request.params.uri === resourceUri) {
    // Use simple test HTML for now
    const htmlPath = path.join(__dirname, "dist", "test-simple.html");
    log(`Reading UI from: ${htmlPath}`);
    const html = await fs.readFile(htmlPath, "utf-8");
    return {
      contents: [
        {
          uri: resourceUri,
          mimeType: RESOURCE_MIME_TYPE,
          text: html,
        },
      ],
    };
  }

  throw new Error(`Unknown resource: ${request.params.uri}`);
});

async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  log("✅ Polymarket MCP App server running on stdio");
}

main().catch((error) => {
  log(`Fatal error: ${error}`);
  process.exit(1);
});
