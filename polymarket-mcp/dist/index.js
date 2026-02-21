import { MCPServer, widget, text } from "mcp-use/server";
import { z } from "zod";
import https from "https";
// Force production mode
process.env.NODE_ENV = "production";
// Redirect stdout to stderr for MCP protocol compliance
const originalWrite = process.stdout.write.bind(process.stdout);
process.stdout.write = (chunk, ...args) => {
    return process.stderr.write(chunk, ...args);
};
const server = new MCPServer({
    name: "polymarket",
    title: "Polymarket Prediction Markets",
    version: "1.0.0",
    baseUrl: process.env.MCP_PUBLIC_URL || undefined,
});
// ============================================================================
// POLYMARKET API HELPERS
// ============================================================================
async function fetchFromPolymarket(endpoint) {
    return new Promise((resolve, reject) => {
        const url = `https://gamma-api.polymarket.com${endpoint}`;
        https
            .get(url, { headers: { "User-Agent": "Mozilla/5.0" } }, (res) => {
            let data = "";
            res.on("data", (chunk) => (data += chunk));
            res.on("end", () => {
                try {
                    resolve(JSON.parse(data));
                }
                catch (e) {
                    reject(new Error("Failed to parse Polymarket response"));
                }
            });
        })
            .on("error", reject);
    });
}
async function getMarkets(limit = 20, closed = false) {
    try {
        return await fetchFromPolymarket(`/markets?limit=${limit}&closed=${closed}`);
    }
    catch (e) {
        console.error("Error fetching markets:", e);
        return [];
    }
}
async function searchMarkets(keyword, limit = 50) {
    try {
        const markets = await getMarkets(limit, false);
        const keywordLower = keyword.toLowerCase();
        return markets.filter(market => (market.question || "").toLowerCase().includes(keywordLower));
    }
    catch (e) {
        console.error("Error searching markets:", e);
        return [];
    }
}
function formatVolume(volume) {
    if (volume > 1000000)
        return `$${(volume / 1000000).toFixed(1)}M`;
    if (volume > 1000)
        return `$${(volume / 1000).toFixed(1)}K`;
    return `$${volume.toFixed(0)}`;
}
function getPriceData(market) {
    const pricesStr = market.outcomePrices || '["0.5", "0.5"]';
    const prices = JSON.parse(pricesStr);
    return {
        yesPrice: parseFloat(prices[0] || "0.5"),
        noPrice: parseFloat(prices[1] || "0.5"),
    };
}
// ============================================================================
// TOOL: SEARCH MARKETS
// ============================================================================
server.tool({
    name: "search_markets",
    description: "Search Polymarket prediction markets by keyword",
    schema: z.object({
        keyword: z.string().describe("Search term (e.g., 'Trump', 'bitcoin', 'AI')"),
        limit: z.number().optional().describe("Max results (default: 10)"),
    }),
}, async ({ keyword, limit = 10 }) => {
    const markets = await searchMarkets(keyword, 50);
    if (markets.length === 0) {
        return text(`No markets found matching "${keyword}"`);
    }
    const displayMarkets = markets.slice(0, limit);
    let result = `SEARCH RESULTS: "${keyword}"\n`;
    result += `Found ${markets.length} market${markets.length !== 1 ? 's' : ''}\n\n`;
    for (let i = 0; i < displayMarkets.length; i++) {
        const market = displayMarkets[i];
        const { yesPrice } = getPriceData(market);
        const volume = market.volumeNum || market.volume || 0;
        result += `${i + 1}. ${market.question}\n`;
        result += `   YES: ${Math.round(yesPrice * 100)}¢`;
        result += ` | Volume: ${formatVolume(volume)}\n\n`;
    }
    result += `\nUse view_market to see detailed data and interactive chart.`;
    return text(result);
});
// ============================================================================
// TOOL: TRENDING MARKETS
// ============================================================================
server.tool({
    name: "trending_markets",
    description: "Get the top trending Polymarket prediction markets",
    schema: z.object({
        limit: z.number().optional().describe("Number of markets (default: 10)"),
    }),
}, async ({ limit = 10 }) => {
    const markets = await getMarkets(limit, false);
    if (markets.length === 0) {
        return text("Unable to fetch markets from Polymarket.");
    }
    let result = "TOP TRENDING MARKETS\n\n";
    for (let i = 0; i < markets.length; i++) {
        const market = markets[i];
        const { yesPrice } = getPriceData(market);
        const volume = market.volumeNum || market.volume || 0;
        result += `${i + 1}. ${market.question}\n`;
        result += `   YES: ${Math.round(yesPrice * 100)}¢`;
        result += ` | Volume: ${formatVolume(volume)}\n\n`;
    }
    return text(result);
});
// ============================================================================
// TOOL: VIEW MARKET (WITH WIDGET)
// ============================================================================
server.tool({
    name: "view_market",
    description: "View detailed prediction market data with interactive visualization",
    schema: z.object({
        keyword: z.string().describe("Search keyword for the market"),
    }),
    widget: {
        name: "market-view",
        invoking: "Loading market data...",
        invoked: "Market loaded",
    },
}, async ({ keyword }) => {
    const markets = await searchMarkets(keyword, 50);
    const marketData = markets[0];
    if (!marketData) {
        return text(`No market found for "${keyword}"`);
    }
    const { yesPrice, noPrice } = getPriceData(marketData);
    const volume = marketData.volumeNum || marketData.volume || 0;
    return widget({
        props: {
            title: marketData.question,
            currentYes: yesPrice,
            currentNo: noPrice,
            volume: formatVolume(volume),
        },
        output: text(`${marketData.question}\nYES: ${Math.round(yesPrice * 100)}¢ | NO: ${Math.round(noPrice * 100)}¢`),
    });
});
server.listen();
