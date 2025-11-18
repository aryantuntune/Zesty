# 🔧 Fix: Graph Analyzer AttributeError

## Error:
```python
AttributeError: 'SocialGraphAnalyzer' object has no attribute 'build_graph'
```

## Root Cause:
Your Windows version is calling `graph_analyzer.build_graph(enriched_accounts)` but the correct method is `analyze_full_network(connections)`.

---

## Fix for main_advanced_v3.py (around line 447-467)

### ❌ WRONG (Your current code):
```python
# === Graph Analysis ===
print("[3/11] 🕸️  Social Network Graph Analysis...")
graph_analyzer.build_graph(enriched_accounts)  # ❌ This method doesn't exist!
```

### ✅ CORRECT (Replace with this):
```python
# === Graph Analysis ===
print("[3/11] 🕸️  Social Network Graph Analysis...")
# Extract connections from accounts (platform-to-platform relationships)
connections = []
for i, acc1 in enumerate(enriched_accounts):
    if not acc1:
        continue
    for j, acc2 in enumerate(enriched_accounts[i+1:], start=i+1):
        if not acc2:
            continue
        # Create connection if accounts might be related (same person)
        platform1 = acc1.get('platform', f'account_{i}')
        platform2 = acc2.get('platform', f'account_{j}')
        connections.append((platform1, platform2))

graph_metrics = graph_analyzer.analyze_full_network(connections) if connections else {
    'network_stats': {'num_nodes': 0, 'num_edges': 0, 'density': 0, 'avg_degree': 0},
    'communities': {'count': 0, 'sizes': [], 'largest_community': 0},
    'central_nodes': [],
    'anomalies': {'isolated_nodes': [], 'bridge_nodes': [], 'outlier_communities': []}
}
```

---

## Quick Fix Steps (On Windows):

### Option 1: Manual Edit

1. Open `main_advanced_v3.py` in VS Code
2. Find line 449 (search for `graph_analyzer.build_graph`)
3. Replace that section with the ✅ CORRECT code above
4. Save the file

### Option 2: Pull Latest Fixed Version

```powershell
# Discard your local changes and pull the fixed version
git fetch origin claude/aiml-portfolio-ideas-0153dmNBEmwKJzAmeZzoQjf4
git reset --hard origin/claude/aiml-portfolio-ideas-0153dmNBEmwKJzAmeZzoQjf4
```

⚠️ **Warning:** This will overwrite your local changes!

---

## What the Fix Does:

### 1. Extracts Connections
Instead of passing raw accounts, we extract connections (relationships) between accounts:
```python
connections = [
    ('github', 'twitter'),
    ('twitter', 'linkedin'),
    ('linkedin', 'instagram')
]
```

### 2. Calls Correct Method
Uses `analyze_full_network(connections)` which:
- Builds the graph internally
- Detects communities
- Calculates centrality
- Finds anomalies
- Returns all metrics

### 3. Provides Fallback
If no connections exist, returns empty structure to prevent crashes.

---

## Available Methods in SocialGraphAnalyzer:

✅ `analyze_full_network(connections)` - **Use this one!**
✅ `build_graph_from_connections(connections)` - Lower level
✅ `detect_communities(graph)` - Community detection
✅ `calculate_centrality(graph)` - Centrality analysis
✅ `find_central_nodes(graph, top_n)` - Find important nodes
✅ `analyze_connection_strength(graph, node1, node2)` - Connection analysis
✅ `detect_anomalies(graph, communities)` - Anomaly detection

❌ `build_graph()` - **Doesn't exist!**
❌ `build_graph(enriched_accounts)` - **Wrong signature!**

---

## After Fixing:

Run the investigation again:
```powershell
python main_advanced_v3.py
```

Expected output:
```
[3/11] 🕸️  Social Network Graph Analysis...
✅ Graph analysis complete
```

---

## Why This Happened:

Your local Windows file has changes that weren't in the force push. You likely:
1. Made the original commit
2. Force pushed
3. Made MORE local edits after pushing
4. Those edits introduced the bug

**Solution:** Either manually fix or pull the correct version from remote.

---

## Need Help?

If you're not sure which code to replace, search for:
```python
graph_analyzer.build_graph
```

Replace that entire section with the ✅ CORRECT code provided above.
