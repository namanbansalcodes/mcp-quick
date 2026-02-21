import { MCPServer, widget, text } from "mcp-use/server";
import { z } from "zod";
import https from "https";
// Force production mode to avoid dev-only features
process.env.NODE_ENV = "production";
// Redirect ALL stdout to stderr (mcp-use logs directly to stdout)
const originalWrite = process.stdout.write.bind(process.stdout);
process.stdout.write = (chunk, ...args) => {
    return process.stderr.write(chunk, ...args);
};
const server = new MCPServer({
    name: "polymarket",
    title: "Polymarket Live Markets",
    version: "1.0.0",
    baseUrl: process.env.MCP_PUBLIC_URL || undefined,
});
// Helper to fetch Polymarket data
async function fetchMarkets(limit = 10) {
    return new Promise((resolve, reject) => {
        const url = `https://gamma-api.polymarket.com/markets?limit=${limit}&closed=false`;
        https
            .get(url, { headers: { "User-Agent": "Mozilla/5.0" } }, (res) => {
            let data = "";
            res.on("data", (chunk) => (data += chunk));
            res.on("end", () => {
                try {
                    resolve(JSON.parse(data));
                }
                catch (e) {
                    reject(e);
                }
            });
        })
            .on("error", reject);
    });
}
async function searchMarket(keyword) {
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
    }
    catch (e) {
        console.error("Error searching markets:", e);
        return null;
    }
}
// Tool: List trending markets
server.tool({
    name: "list_trending_markets",
    description: "List the top trending Polymarket predictions",
    schema: z.object({}),
}, async () => {
    const markets = await fetchMarkets(10);
    if (!markets || markets.length === 0) {
        return text("Unable to fetch markets from Polymarket API.");
    }
    let result = "🔥 Top Trending Polymarket Predictions:\n\n";
    for (let i = 0; i < markets.length; i++) {
        const market = markets[i];
        const question = market.question || "Unknown";
        const pricesStr = market.outcomePrices || '["0.5", "0.5"]';
        const prices = JSON.parse(pricesStr);
        const volume = market.volumeNum || market.volume || 0;
        const volumeStr = volume > 1000000
            ? `$${(volume / 1000000).toFixed(1)}M`
            : `$${(volume / 1000).toFixed(0)}K`;
        const yesPrice = parseFloat(prices[0] || "0.5");
        const yesPct = Math.round(yesPrice * 100);
        result += `${i + 1}. ${question}\n`;
        result += `   💹 YES: ${yesPct}¢ | 💰 Volume: ${volumeStr}\n\n`;
    }
    result += "\nUse view_market(keyword) to see detailed graph!";
    return text(result);
});
// Tool: View market with simplified widget
server.tool({
    name: "view_market",
    description: "View live data for a Polymarket prediction",
    schema: z.object({
        keyword: z.string().describe("Search keyword for the market"),
    }),
    widget: {
        name: "market-view",
        invoking: "Loading market data...",
        invoked: "Market loaded",
    },
}, async ({ keyword }) => {
    const marketData = await searchMarket(keyword);
    if (!marketData) {
        return text(`No market found for "${keyword}"`);
    }
    const outcomesStr = marketData.outcomes || '["Yes", "No"]';
    const pricesStr = marketData.outcomePrices || '["0.5", "0.5"]';
    const prices = JSON.parse(pricesStr);
    const currentYes = parseFloat(prices[0] || "0.5");
    const currentNo = parseFloat(prices[1] || "0.5");
    const volume = marketData.volumeNum || marketData.volume || 0;
    const volumeStr = volume > 1000000
        ? `$${(volume / 1000000).toFixed(1)}M`
        : volume > 1000
            ? `$${(volume / 1000).toFixed(1)}K`
            : `$${volume.toFixed(0)}`;
    return widget({
        props: {
            title: marketData.question,
            currentYes,
            currentNo,
            volume: volumeStr,
        },
        output: text(`Showing market: ${marketData.question}`),
    });
});
// Tool: Place bet (simulated)
server.tool({
    name: "place_bet",
    description: "Simulate placing a bet on a market",
    schema: z.object({
        market_title: z.string().describe("Market question"),
        outcome: z.enum(["YES", "NO"]).describe("Bet outcome"),
        amount: z.number().describe("Bet amount in USD"),
    }),
}, async ({ market_title, outcome, amount }) => {
    return text(`✅ Placed $${amount} bet on ${outcome} for "${market_title}"`);
});
server.listen();
