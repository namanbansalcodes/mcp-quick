import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useWidget } from "mcp-use/react";
import { z } from "zod";
const propsSchema = z.object({
    title: z.string(),
    currentYes: z.number(),
    currentNo: z.number(),
    volume: z.string(),
});
export const widgetMetadata = {
    description: "Display Polymarket prediction",
    props: propsSchema,
    exposeAsTool: false,
};
export default function MarketView() {
    const { props, isPending } = useWidget();
    if (isPending) {
        return (_jsx("div", { style: {
                padding: 60,
                textAlign: "center",
                background: '#0a0e27',
                minHeight: '100vh',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
            }, children: _jsx("div", { style: {
                    fontSize: 18,
                    color: "#00ff88",
                    fontFamily: 'monospace',
                    letterSpacing: '0.1em'
                }, children: "LOADING MARKET DATA..." }) }));
    }
    const yesPct = Math.round(props.currentYes * 100);
    const noPct = Math.round(props.currentNo * 100);
    const yesDecimal = (props.currentYes * 100).toFixed(2);
    const noDecimal = (props.currentNo * 100).toFixed(2);
    return (_jsx("div", { style: {
            fontFamily: '"JetBrains Mono", "Fira Code", "Consolas", monospace',
            background: '#0a0e27',
            padding: 0,
            minHeight: '100vh',
            color: '#e0e0e0'
        }, children: _jsxs("div", { style: {
                maxWidth: 1400,
                margin: '0 auto',
                padding: 40
            }, children: [_jsxs("div", { style: {
                        borderBottom: '1px solid #1a1f3a',
                        paddingBottom: 25,
                        marginBottom: 35
                    }, children: [_jsx("div", { style: {
                                fontSize: 11,
                                color: '#00ff88',
                                letterSpacing: '0.15em',
                                marginBottom: 10,
                                textTransform: 'uppercase',
                                fontWeight: 600
                            }, children: "POLYMARKET PREDICTION MARKET" }), _jsx("h1", { style: {
                                fontSize: 28,
                                marginBottom: 0,
                                color: '#ffffff',
                                fontWeight: 400,
                                lineHeight: 1.4,
                                letterSpacing: '-0.02em'
                            }, children: props.title })] }), _jsxs("div", { style: {
                        display: 'grid',
                        gridTemplateColumns: '1fr 1fr 1fr',
                        gap: 25,
                        marginBottom: 40
                    }, children: [_jsxs("div", { style: {
                                padding: 30,
                                background: 'linear-gradient(135deg, rgba(16, 185, 129, 0.1) 0%, rgba(16, 185, 129, 0.05) 100%)',
                                border: '1px solid rgba(16, 185, 129, 0.3)',
                                borderRadius: 4
                            }, children: [_jsx("div", { style: {
                                        fontSize: 11,
                                        color: '#10b981',
                                        marginBottom: 15,
                                        letterSpacing: '0.15em',
                                        fontWeight: 600
                                    }, children: "LONG / YES" }), _jsxs("div", { style: {
                                        fontSize: 52,
                                        fontWeight: 700,
                                        color: '#10b981',
                                        lineHeight: 1,
                                        marginBottom: 10,
                                        fontFeatureSettings: '"tnum"'
                                    }, children: [yesPct, _jsx("span", { style: { fontSize: 32, opacity: 0.7 }, children: "\u00A2" })] }), _jsxs("div", { style: {
                                        fontSize: 13,
                                        color: '#10b981',
                                        opacity: 0.6,
                                        fontFeatureSettings: '"tnum"'
                                    }, children: [yesDecimal, "%"] })] }), _jsxs("div", { style: {
                                padding: 30,
                                background: 'linear-gradient(135deg, rgba(239, 68, 68, 0.1) 0%, rgba(239, 68, 68, 0.05) 100%)',
                                border: '1px solid rgba(239, 68, 68, 0.3)',
                                borderRadius: 4
                            }, children: [_jsx("div", { style: {
                                        fontSize: 11,
                                        color: '#ef4444',
                                        marginBottom: 15,
                                        letterSpacing: '0.15em',
                                        fontWeight: 600
                                    }, children: "SHORT / NO" }), _jsxs("div", { style: {
                                        fontSize: 52,
                                        fontWeight: 700,
                                        color: '#ef4444',
                                        lineHeight: 1,
                                        marginBottom: 10,
                                        fontFeatureSettings: '"tnum"'
                                    }, children: [noPct, _jsx("span", { style: { fontSize: 32, opacity: 0.7 }, children: "\u00A2" })] }), _jsxs("div", { style: {
                                        fontSize: 13,
                                        color: '#ef4444',
                                        opacity: 0.6,
                                        fontFeatureSettings: '"tnum"'
                                    }, children: [noDecimal, "%"] })] }), _jsxs("div", { style: {
                                padding: 30,
                                background: 'linear-gradient(135deg, rgba(0, 255, 136, 0.1) 0%, rgba(0, 255, 136, 0.05) 100%)',
                                border: '1px solid rgba(0, 255, 136, 0.3)',
                                borderRadius: 4
                            }, children: [_jsx("div", { style: {
                                        fontSize: 11,
                                        color: '#00ff88',
                                        marginBottom: 15,
                                        letterSpacing: '0.15em',
                                        fontWeight: 600
                                    }, children: "TRADING VOLUME" }), _jsx("div", { style: {
                                        fontSize: 52,
                                        fontWeight: 700,
                                        color: '#00ff88',
                                        lineHeight: 1,
                                        fontFeatureSettings: '"tnum"'
                                    }, children: props.volume })] })] }), _jsx("div", { style: {
                        padding: 25,
                        background: 'rgba(255, 255, 255, 0.03)',
                        border: '1px solid #1a1f3a',
                        borderRadius: 4
                    }, children: _jsxs("div", { style: {
                            display: 'grid',
                            gridTemplateColumns: '1fr 1fr',
                            gap: 30
                        }, children: [_jsxs("div", { children: [_jsx("div", { style: {
                                            fontSize: 11,
                                            color: '#666',
                                            marginBottom: 8,
                                            letterSpacing: '0.1em'
                                        }, children: "MARKET TYPE" }), _jsx("div", { style: { color: '#e0e0e0', fontSize: 14 }, children: "Binary Prediction Market" })] }), _jsxs("div", { children: [_jsx("div", { style: {
                                            fontSize: 11,
                                            color: '#666',
                                            marginBottom: 8,
                                            letterSpacing: '0.1em'
                                        }, children: "STATUS" }), _jsx("div", { style: { color: '#00ff88', fontSize: 14 }, children: "ACTIVE" })] })] }) }), _jsx("div", { style: {
                        marginTop: 30,
                        paddingTop: 20,
                        borderTop: '1px solid #1a1f3a',
                        fontSize: 11,
                        color: '#666',
                        letterSpacing: '0.05em'
                    }, children: "POWERED BY POLYMARKET" })] }) }));
}
