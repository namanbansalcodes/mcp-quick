import { useWidget } from "mcp-use/react";
import { z } from "zod";

const propsSchema = z.object({
  title: z.string(),
  currentYes: z.number(),
  currentNo: z.number(),
  volume: z.string(),
});

type Props = z.infer<typeof propsSchema>;

export const widgetMetadata = {
  description: "Display Polymarket prediction",
  props: propsSchema,
  exposeAsTool: false,
};

export default function MarketView() {
  const { props, isPending } = useWidget<Props>();

  if (isPending) {
    return (
      <div style={{
        padding: 60,
        textAlign: "center",
        background: '#0a0e27',
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center'
      }}>
        <div style={{
          fontSize: 18,
          color: "#00ff88",
          fontFamily: 'monospace',
          letterSpacing: '0.1em'
        }}>LOADING MARKET DATA...</div>
      </div>
    );
  }

  const yesPct = Math.round(props.currentYes * 100);
  const noPct = Math.round(props.currentNo * 100);
  const yesDecimal = (props.currentYes * 100).toFixed(2);
  const noDecimal = (props.currentNo * 100).toFixed(2);

  return (
    <div style={{
      fontFamily: '"JetBrains Mono", "Fira Code", "Consolas", monospace',
      background: '#0a0e27',
      padding: 0,
      minHeight: '100vh',
      color: '#e0e0e0'
    }}>
      <div style={{
        maxWidth: 1400,
        margin: '0 auto',
        padding: 40
      }}>
        {/* Header */}
        <div style={{
          borderBottom: '1px solid #1a1f3a',
          paddingBottom: 25,
          marginBottom: 35
        }}>
          <div style={{
            fontSize: 11,
            color: '#00ff88',
            letterSpacing: '0.15em',
            marginBottom: 10,
            textTransform: 'uppercase',
            fontWeight: 600
          }}>
            POLYMARKET PREDICTION MARKET
          </div>
          <h1 style={{
            fontSize: 28,
            marginBottom: 0,
            color: '#ffffff',
            fontWeight: 400,
            lineHeight: 1.4,
            letterSpacing: '-0.02em'
          }}>
            {props.title}
          </h1>
        </div>

        {/* Main Stats Grid */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: '1fr 1fr 1fr',
          gap: 25,
          marginBottom: 40
        }}>
          {/* YES Card */}
          <div style={{
            padding: 30,
            background: 'linear-gradient(135deg, rgba(16, 185, 129, 0.1) 0%, rgba(16, 185, 129, 0.05) 100%)',
            border: '1px solid rgba(16, 185, 129, 0.3)',
            borderRadius: 4
          }}>
            <div style={{
              fontSize: 11,
              color: '#10b981',
              marginBottom: 15,
              letterSpacing: '0.15em',
              fontWeight: 600
            }}>
              LONG / YES
            </div>
            <div style={{
              fontSize: 52,
              fontWeight: 700,
              color: '#10b981',
              lineHeight: 1,
              marginBottom: 10,
              fontFeatureSettings: '"tnum"'
            }}>
              {yesPct}<span style={{ fontSize: 32, opacity: 0.7 }}>¢</span>
            </div>
            <div style={{
              fontSize: 13,
              color: '#10b981',
              opacity: 0.6,
              fontFeatureSettings: '"tnum"'
            }}>
              {yesDecimal}%
            </div>
          </div>

          {/* NO Card */}
          <div style={{
            padding: 30,
            background: 'linear-gradient(135deg, rgba(239, 68, 68, 0.1) 0%, rgba(239, 68, 68, 0.05) 100%)',
            border: '1px solid rgba(239, 68, 68, 0.3)',
            borderRadius: 4
          }}>
            <div style={{
              fontSize: 11,
              color: '#ef4444',
              marginBottom: 15,
              letterSpacing: '0.15em',
              fontWeight: 600
            }}>
              SHORT / NO
            </div>
            <div style={{
              fontSize: 52,
              fontWeight: 700,
              color: '#ef4444',
              lineHeight: 1,
              marginBottom: 10,
              fontFeatureSettings: '"tnum"'
            }}>
              {noPct}<span style={{ fontSize: 32, opacity: 0.7 }}>¢</span>
            </div>
            <div style={{
              fontSize: 13,
              color: '#ef4444',
              opacity: 0.6,
              fontFeatureSettings: '"tnum"'
            }}>
              {noDecimal}%
            </div>
          </div>

          {/* Volume Card */}
          <div style={{
            padding: 30,
            background: 'linear-gradient(135deg, rgba(0, 255, 136, 0.1) 0%, rgba(0, 255, 136, 0.05) 100%)',
            border: '1px solid rgba(0, 255, 136, 0.3)',
            borderRadius: 4
          }}>
            <div style={{
              fontSize: 11,
              color: '#00ff88',
              marginBottom: 15,
              letterSpacing: '0.15em',
              fontWeight: 600
            }}>
              TRADING VOLUME
            </div>
            <div style={{
              fontSize: 52,
              fontWeight: 700,
              color: '#00ff88',
              lineHeight: 1,
              fontFeatureSettings: '"tnum"'
            }}>
              {props.volume}
            </div>
          </div>
        </div>

        {/* Market Info */}
        <div style={{
          padding: 25,
          background: 'rgba(255, 255, 255, 0.03)',
          border: '1px solid #1a1f3a',
          borderRadius: 4
        }}>
          <div style={{
            display: 'grid',
            gridTemplateColumns: '1fr 1fr',
            gap: 30
          }}>
            <div>
              <div style={{
                fontSize: 11,
                color: '#666',
                marginBottom: 8,
                letterSpacing: '0.1em'
              }}>
                MARKET TYPE
              </div>
              <div style={{ color: '#e0e0e0', fontSize: 14 }}>
                Binary Prediction Market
              </div>
            </div>
            <div>
              <div style={{
                fontSize: 11,
                color: '#666',
                marginBottom: 8,
                letterSpacing: '0.1em'
              }}>
                STATUS
              </div>
              <div style={{ color: '#00ff88', fontSize: 14 }}>
                ACTIVE
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div style={{
          marginTop: 30,
          paddingTop: 20,
          borderTop: '1px solid #1a1f3a',
          fontSize: 11,
          color: '#666',
          letterSpacing: '0.05em'
        }}>
          POWERED BY POLYMARKET
        </div>
      </div>
    </div>
  );
}
