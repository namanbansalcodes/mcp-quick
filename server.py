"""
MCP Gatekeeper - Policy-enforced tool server with approval workflows.

Built for the Manufact (mcp-use) Hackathon, Feb 2026.

Run:  python server.py
Test: Use mcp-use Inspector at https://inspector.mcp-use.com
      or locally with: fastmcp dev server.py
"""

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated

from fastmcp import FastMCP

# ── Paths ────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent.resolve()
SANDBOX_DIR = BASE_DIR / "sandbox"
POLICY_FILE = BASE_DIR / "policy.json"

SANDBOX_DIR.mkdir(exist_ok=True)

# ── In-memory state ──────────────────────────────────────────────────
pending_actions: dict[str, dict] = {}
audit_entries: list[dict] = []

# ── Policy engine ────────────────────────────────────────────────────
DEFAULT_POLICY = {
    "read_file":   {"risk_level": "SAFE",      "default_action": "allow",            "allow_approval": False},
    "write_file":  {"risk_level": "SENSITIVE",  "default_action": "require_approval", "allow_approval": True},
    "delete_file": {"risk_level": "DANGEROUS",  "default_action": "block",            "allow_approval": True},
    "run_shell":   {"risk_level": "DANGEROUS",  "default_action": "block",            "allow_approval": False},
}


def load_policy() -> dict:
    """Load policy from file or use defaults."""
    if POLICY_FILE.exists():
        with open(POLICY_FILE) as f:
            return json.load(f)
    return DEFAULT_POLICY


def get_tool_policy(tool_name: str) -> dict:
    """Get policy for a specific tool."""
    policy = load_policy()
    return policy.get(tool_name, {
        "risk_level": "DANGEROUS",
        "default_action": "block",
        "allow_approval": False,
    })


# ── Sandbox safety ───────────────────────────────────────────────────
def safe_path(user_path: str) -> Path:
    """Resolve a user-provided path inside sandbox. Blocks traversal."""
    target = (SANDBOX_DIR / user_path).resolve()
    if not str(target).startswith(str(SANDBOX_DIR.resolve())):
        raise ValueError(f"Path traversal blocked: {user_path}")
    return target


# ── Audit log helper ─────────────────────────────────────────────────
def audit(tool: str, args: dict, decision: str, risk: str, detail: str = "") -> dict:
    """Record an audit event and return it."""
    entry = {
        "id": uuid.uuid4().hex[:8],
        "ts": datetime.now(timezone.utc).isoformat(),
        "tool": tool,
        "args": _sanitize_args(args),
        "risk": risk,
        "decision": decision,
        "detail": detail,
    }
    audit_entries.append(entry)
    return entry


def _sanitize_args(args: dict) -> dict:
    """Truncate large values for audit readability."""
    out = {}
    for k, v in args.items():
        if isinstance(v, str) and len(v) > 200:
            out[k] = v[:200] + f"...({len(v)} bytes)"
        else:
            out[k] = v
    return out


# ── Effect descriptions ──────────────────────────────────────────────
def describe_effect(tool: str, args: dict) -> str:
    if tool == "read_file":
        return f"Read file sandbox/{args.get('path', '?')}"
    if tool == "write_file":
        n = len(args.get("content", ""))
        return f"Write {n} bytes to sandbox/{args.get('path', '?')}"
    if tool == "delete_file":
        return f"PERMANENTLY delete sandbox/{args.get('path', '?')}"
    if tool == "run_shell":
        return f"Execute shell: {args.get('command', '?')}"
    return "Unknown"


# ── Direct execution (bypasses policy) ───────────────────────────────
def _exec(tool: str, args: dict) -> str:
    if tool == "read_file":
        p = safe_path(args["path"])
        if not p.exists():
            return f"Error: file not found: {args['path']}"
        return p.read_text()

    if tool == "write_file":
        p = safe_path(args["path"])
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(args["content"])
        return f"OK: wrote {len(args['content'])} bytes to {args['path']}"

    if tool == "delete_file":
        p = safe_path(args["path"])
        if not p.exists():
            return f"Error: file not found: {args['path']}"
        p.unlink()
        return f"OK: deleted {args['path']}"

    return "Error: cannot execute"


# ── Policy enforcement helper ────────────────────────────────────────
def _create_pending(tool: str, args: dict, risk: str) -> str:
    """Create a pending action and return JSON response."""
    aid = uuid.uuid4().hex[:8]
    pending_actions[aid] = {
        "id": aid,
        "tool_name": tool,
        "args": args,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "risk_level": risk,
        "proposed_effect": describe_effect(tool, args),
        "status": "PENDING",
    }
    audit(tool, args, "PENDING_APPROVAL", risk, f"action_id={aid}")
    return json.dumps({
        "status": "APPROVAL_REQUIRED",
        "action_id": aid,
        "risk_level": risk,
        "proposed_effect": describe_effect(tool, args),
        "instruction": f"Use approve('{aid}') to execute or deny('{aid}') to reject.",
    }, indent=2)


# ══════════════════════════════════════════════════════════════════════
#  MCP SERVER
# ══════════════════════════════════════════════════════════════════════

mcp = FastMCP(
    "MCP Gatekeeper",
    instructions=(
        "MCP Gatekeeper: a policy-enforced tool server.\n"
        "Tools are risk-classified: SAFE (auto-execute), SENSITIVE (needs approval), DANGEROUS (blocked).\n"
        "Use list_pending/approve/deny to manage actions. Use audit_log to review history.\n"
        "All filesystem ops are sandboxed to ./sandbox/."
    ),
)


# ── File tools ───────────────────────────────────────────────────────

@mcp.tool()
def read_file(path: Annotated[str, "Relative path inside sandbox"]) -> str:
    """Read a file from the sandbox. [SAFE - executes immediately]"""
    try:
        target = safe_path(path)
        if not target.exists():
            audit("read_file", {"path": path}, "ERROR", "SAFE", "not found")
            return f"Error: file not found: {path}"
        content = target.read_text()
        audit("read_file", {"path": path}, "EXECUTED", "SAFE", f"{len(content)}B")
        return content
    except ValueError as e:
        audit("read_file", {"path": path}, "BLOCKED", "DANGEROUS", str(e))
        return f"BLOCKED: {e}"


@mcp.tool()
def write_file(
    path: Annotated[str, "Relative path inside sandbox"],
    content: Annotated[str, "Content to write"],
) -> str:
    """Write a file in the sandbox. [SENSITIVE - requires approval]"""
    try:
        safe_path(path)  # validate early
        policy = get_tool_policy("write_file")
        risk = policy["risk_level"]
        action = policy["default_action"]

        if action == "allow":
            result = _exec("write_file", {"path": path, "content": content})
            audit("write_file", {"path": path, "content_length": len(content)}, "EXECUTED", risk)
            return result

        if action in ("require_approval", "block") and policy.get("allow_approval", False):
            return _create_pending("write_file", {"path": path, "content": content}, risk)

        audit("write_file", {"path": path}, "BLOCKED", risk, "policy: no approval allowed")
        return "BLOCKED: write_file is blocked by policy"

    except ValueError as e:
        audit("write_file", {"path": path}, "BLOCKED", "DANGEROUS", str(e))
        return f"BLOCKED: {e}"


@mcp.tool()
def delete_file(path: Annotated[str, "Relative path inside sandbox"]) -> str:
    """Delete a file from the sandbox. [DANGEROUS - blocked, approvable]"""
    try:
        safe_path(path)  # validate early
        policy = get_tool_policy("delete_file")
        risk = policy["risk_level"]
        action = policy["default_action"]

        if action == "allow":
            result = _exec("delete_file", {"path": path})
            audit("delete_file", {"path": path}, "EXECUTED", risk)
            return result

        if policy.get("allow_approval", False):
            return _create_pending("delete_file", {"path": path}, risk)

        audit("delete_file", {"path": path}, "BLOCKED", risk, "permanently blocked")
        return "BLOCKED: delete_file is permanently blocked"

    except ValueError as e:
        audit("delete_file", {"path": path}, "BLOCKED", "DANGEROUS", str(e))
        return f"BLOCKED: {e}"


@mcp.tool()
def run_shell(command: Annotated[str, "Shell command to execute"]) -> str:
    """Execute a shell command. [DANGEROUS - ALWAYS blocked, NEVER approvable]"""
    audit("run_shell", {"command": command}, "BLOCKED", "DANGEROUS",
          "Shell execution permanently forbidden")
    return json.dumps({
        "status": "BLOCKED",
        "risk_level": "DANGEROUS",
        "message": "run_shell is PERMANENTLY blocked. This can never be approved.",
    }, indent=2)


# ── Approval workflow tools ──────────────────────────────────────────

@mcp.tool()
def list_pending() -> str:
    """List all pending actions awaiting approval."""
    items = [a for a in pending_actions.values() if a["status"] == "PENDING"]
    if not items:
        return "No pending actions."
    return json.dumps(items, indent=2)


@mcp.tool()
def approve(action_id: Annotated[str, "ID of the pending action to approve"]) -> str:
    """Approve and execute a pending action."""
    if action_id not in pending_actions:
        return f"Error: action '{action_id}' not found"

    action = pending_actions[action_id]
    if action["status"] != "PENDING":
        return f"Error: action '{action_id}' is already {action['status']}"

    try:
        result = _exec(action["tool_name"], action["args"])
        action["status"] = "APPROVED"
        audit(action["tool_name"], action["args"], "APPROVED_EXECUTED",
              action["risk_level"], f"aid={action_id} | {result}")
        return json.dumps({
            "status": "APPROVED_AND_EXECUTED",
            "action_id": action_id,
            "result": result,
        }, indent=2)
    except Exception as e:
        action["status"] = "ERROR"
        audit(action["tool_name"], action["args"], "ERROR",
              action["risk_level"], str(e))
        return f"Execution error: {e}"


@mcp.tool()
def deny(action_id: Annotated[str, "ID of the pending action to deny"]) -> str:
    """Deny and discard a pending action."""
    if action_id not in pending_actions:
        return f"Error: action '{action_id}' not found"

    action = pending_actions[action_id]
    if action["status"] != "PENDING":
        return f"Error: action '{action_id}' is already {action['status']}"

    action["status"] = "DENIED"
    audit(action["tool_name"], action["args"], "DENIED",
          action["risk_level"], f"aid={action_id} denied by user")
    return json.dumps({
        "status": "DENIED",
        "action_id": action_id,
        "tool": action["tool_name"],
        "message": "Action denied. It will not be executed.",
    }, indent=2)


# ── Observability tools ──────────────────────────────────────────────

@mcp.tool()
def audit_log(limit: Annotated[int, "Max entries to return"] = 25) -> str:
    """View audit log of all actions and decisions (most recent first)."""
    if not audit_entries:
        return "Audit log is empty."
    recent = list(reversed(audit_entries[-limit:]))
    return json.dumps(recent, indent=2)


@mcp.tool()
def get_policy() -> str:
    """View the current policy configuration for all tools."""
    return json.dumps(load_policy(), indent=2)


@mcp.tool()
def get_dashboard() -> str:
    """Get a full dashboard: policy, pending actions, and recent audit events."""
    pending = [a for a in pending_actions.values() if a["status"] == "PENDING"]
    recent = list(reversed(audit_entries[-10:]))

    RISK_BADGE = {"SAFE": "[SAFE]", "SENSITIVE": "[SENSITIVE]", "DANGEROUS": "[DANGEROUS]"}

    lines = []
    lines.append("=" * 60)
    lines.append("  MCP GATEKEEPER DASHBOARD")
    lines.append("=" * 60)

    # Policy summary
    lines.append("\n--- POLICY ---")
    for tool_name, p in load_policy().items():
        badge = RISK_BADGE.get(p["risk_level"], "[?]")
        lines.append(f"  {tool_name:15s}  {badge:14s}  action={p['default_action']:20s}  approvable={p.get('allow_approval', False)}")

    # Pending actions
    lines.append(f"\n--- PENDING ACTIONS ({len(pending)}) ---")
    if not pending:
        lines.append("  (none)")
    for a in pending:
        badge = RISK_BADGE.get(a["risk_level"], "[?]")
        lines.append(f"  [{a['id']}] {badge} {a['tool_name']}  ->  {a['proposed_effect']}")
        lines.append(f"           created: {a['created_at']}")

    # Recent audit
    lines.append(f"\n--- RECENT AUDIT ({len(recent)} of {len(audit_entries)} total) ---")
    if not recent:
        lines.append("  (none)")
    for e in recent:
        lines.append(f"  {e['ts']}  {e['tool']:15s}  {e['decision']:20s}  {e['risk']:10s}  {e.get('detail', '')[:60]}")

    lines.append("\n" + "=" * 60)
    return "\n".join(lines)


# ── MCP App UI resource (HTML widget) ────────────────────────────────

DASHBOARD_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>MCP Gatekeeper</title>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
         background: #0d1117; color: #c9d1d9; padding: 20px; }
  h1 { color: #58a6ff; margin-bottom: 4px; font-size: 1.5rem; }
  h2 { color: #8b949e; font-size: 1rem; margin: 16px 0 8px; border-bottom: 1px solid #21262d; padding-bottom: 4px; }
  .subtitle { color: #8b949e; font-size: 0.85rem; margin-bottom: 16px; }
  .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-top: 12px; }
  .card { background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 16px; }
  .badge { display: inline-block; padding: 2px 8px; border-radius: 12px; font-size: 0.75rem; font-weight: 600; }
  .badge-safe { background: #238636; color: #fff; }
  .badge-sensitive { background: #d29922; color: #000; }
  .badge-dangerous { background: #da3633; color: #fff; }
  .pending-item { background: #1c2128; border: 1px solid #30363d; border-radius: 6px; padding: 12px; margin: 8px 0; cursor: pointer; }
  .pending-item:hover { border-color: #58a6ff; }
  .pending-item .meta { color: #8b949e; font-size: 0.8rem; margin-top: 4px; }
  .btn { padding: 6px 16px; border: none; border-radius: 6px; cursor: pointer; font-weight: 600; font-size: 0.85rem; margin-right: 8px; }
  .btn-approve { background: #238636; color: #fff; }
  .btn-approve:hover { background: #2ea043; }
  .btn-deny { background: #da3633; color: #fff; }
  .btn-deny:hover { background: #f85149; }
  .btn-refresh { background: #30363d; color: #c9d1d9; margin-bottom: 12px; }
  .btn-refresh:hover { background: #484f58; }
  table { width: 100%; border-collapse: collapse; font-size: 0.8rem; }
  th { text-align: left; color: #8b949e; padding: 6px 8px; border-bottom: 1px solid #30363d; }
  td { padding: 6px 8px; border-bottom: 1px solid #21262d; }
  .policy-row { display: flex; align-items: center; gap: 12px; padding: 6px 0; }
  .policy-tool { font-family: monospace; width: 120px; }
  .policy-action { color: #8b949e; font-size: 0.85rem; }
  .empty { color: #484f58; font-style: italic; padding: 12px; }
  pre { background: #1c2128; padding: 8px; border-radius: 4px; overflow-x: auto; font-size: 0.8rem; }
  code { font-family: 'SF Mono', Monaco, monospace; }
</style>
</head>
<body>
  <h1>MCP Gatekeeper</h1>
  <p class="subtitle">Policy-enforced tool access control &middot; Manufact Hackathon 2026</p>

  <div class="grid">
    <div>
      <div class="card">
        <h2>Policy Configuration</h2>
        <div id="policy"></div>
      </div>
      <div class="card" style="margin-top: 16px;">
        <h2>Pending Actions</h2>
        <div id="pending"></div>
      </div>
    </div>
    <div>
      <div class="card">
        <h2>Action Detail</h2>
        <div id="detail"><p class="empty">Select a pending action to view details.</p></div>
      </div>
    </div>
  </div>

  <div class="card" style="margin-top: 16px;">
    <h2>Audit Log</h2>
    <div style="max-height: 300px; overflow-y: auto;">
      <table>
        <thead><tr><th>Time</th><th>Tool</th><th>Risk</th><th>Decision</th><th>Detail</th></tr></thead>
        <tbody id="audit"></tbody>
      </table>
    </div>
  </div>

<script>
const POLICY = __POLICY__;
const PENDING = __PENDING__;
const AUDIT = __AUDIT__;

function badge(risk) {
  const c = {SAFE:'badge-safe',SENSITIVE:'badge-sensitive',DANGEROUS:'badge-dangerous'}[risk]||'';
  return '<span class="badge '+c+'">'+risk+'</span>';
}

// Policy
(function() {
  const el = document.getElementById('policy');
  let h = '';
  for (const [t, p] of Object.entries(POLICY)) {
    h += '<div class="policy-row"><span class="policy-tool">'+t+'</span> '+badge(p.risk_level)+
         ' <span class="policy-action">'+p.default_action+' | approvable: '+(p.allow_approval||false)+'</span></div>';
  }
  el.innerHTML = h;
})();

// Pending
(function() {
  const el = document.getElementById('pending');
  if (!PENDING.length) { el.innerHTML = '<p class="empty">No pending actions.</p>'; return; }
  let h = '';
  for (const a of PENDING) {
    h += '<div class="pending-item" onclick="sel(\''+a.id+'\')"><strong>'+a.tool_name+'</strong> '+
         badge(a.risk_level)+'<div class="meta">'+a.proposed_effect+'</div>'+
         '<div class="meta">ID: '+a.id+' &middot; '+a.created_at+'</div></div>';
  }
  el.innerHTML = h;
})();

function sel(id) {
  const a = PENDING.find(x => x.id === id);
  if (!a) return;
  document.getElementById('detail').innerHTML =
    '<p><strong>Tool:</strong> <code>'+a.tool_name+'</code></p>'+
    '<p><strong>Risk:</strong> '+badge(a.risk_level)+'</p>'+
    '<p><strong>Effect:</strong> '+a.proposed_effect+'</p>'+
    '<p><strong>Args:</strong></p><pre>'+JSON.stringify(a.args,null,2)+'</pre>'+
    '<p><strong>Created:</strong> '+a.created_at+'</p>'+
    '<div style="margin-top:12px">'+
    '<button class="btn btn-approve">Approve</button>'+
    '<button class="btn btn-deny">Deny</button></div>'+
    '<p class="meta" style="margin-top:8px">In Inspector: <code>approve("'+a.id+'")</code> or <code>deny("'+a.id+'")</code></p>';
}

// Audit
(function() {
  const el = document.getElementById('audit');
  if (!AUDIT.length) { el.innerHTML = '<tr><td colspan="5" class="empty">No events yet.</td></tr>'; return; }
  let h = '';
  for (const e of AUDIT) {
    h += '<tr><td>'+(e.ts||'')+'</td><td><code>'+e.tool+'</code></td><td>'+badge(e.risk)+
         '</td><td>'+e.decision+'</td><td>'+(e.detail||'').substring(0,80)+'</td></tr>';
  }
  el.innerHTML = h;
})();
</script>
</body>
</html>"""


@mcp.tool()
def get_dashboard_ui() -> str:
    """Get an interactive HTML dashboard (MCP App UI) for the Gatekeeper.
    Returns self-contained HTML with current state embedded.
    Call again after approve/deny to get updated view."""
    pending = [a for a in pending_actions.values() if a["status"] == "PENDING"]
    recent = list(reversed(audit_entries[-20:]))
    policy = load_policy()

    html = DASHBOARD_HTML
    html = html.replace("__POLICY__", json.dumps(policy))
    html = html.replace("__PENDING__", json.dumps(pending))
    html = html.replace("__AUDIT__", json.dumps(recent))
    return html


# ══════════════════════════════════════════════════════════════════════
#  ENTRY POINT
# ══════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    mcp.run()
