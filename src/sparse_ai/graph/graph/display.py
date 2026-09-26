import os
import shutil
import tempfile
import uuid
import warnings
import webbrowser
from textwrap import dedent


class GraphDisplay:
  COLOR_START = "#2E7D32"
  FILL_START = "#4CAF50"
  COLOR_END = "#C62828"
  FILL_END = "#EF5350"
  COLOR_NODE = "#1565C0"
  FILL_NODE = "#E3F2FD"
  COLOR_ROUTER = "#E65100"
  FILL_ROUTER = "#FFF3E0"
  COLOR_EDGE = "#455A64"

  @staticmethod
  def to_dot(graph) -> str:
    """Generates standard Graphviz DOT language representation."""
    lines = [
        "digraph AgentGraph {",
        "    rankdir=TB;",
        "    splines=polyline;",
        '    nodesep="0.8";',
        '    ranksep="1.0";',
        "    concentrate=false;",
        '    bgcolor="transparent";',
        (
            '    node [fontname="Segoe UI, Helvetica, sans-serif", fontsize=12,'
            ' style="filled,rounded", margin="0.2,0.1", penwidth=1.6];'
        ),
        (
            '    edge [fontname="Segoe UI, Helvetica, sans-serif", fontsize=10,'
            ' color="#455A64", penwidth=1.3, arrowsize=0.85];'
        ),
    ]

    router_names = {e.start for e in graph.edges if e.router is not None}

    # Terminal nodes
    lines.append(
        f'    START [label="START", shape=box,'
        f' fillcolor="{GraphDisplay.FILL_START}",'
        f' color="{GraphDisplay.COLOR_START}", fontcolor="#FFFFFF",'
        ' style="filled,rounded"];'
    )
    lines.append(
        f'    END [label="END", shape=box, fillcolor="{GraphDisplay.FILL_END}",'
        f' color="{GraphDisplay.COLOR_END}", fontcolor="#FFFFFF",'
        ' style="filled,rounded"];'
    )

    # Graph nodes
    for name in graph.nodes:
      label = name.replace("_", " ").title()
      is_entry = name == graph._entry_point
      penwidth = "2.6" if is_entry else "1.6"

      if name in router_names:
        lines.append(
            f'    {name} [label="  {label}  ", shape=diamond, style=filled,'
            f' fillcolor="{GraphDisplay.FILL_ROUTER}",'
            f' color="{GraphDisplay.COLOR_ROUTER}", fontcolor="#BF360C",'
            f" penwidth={penwidth}];"
        )
      else:
        lines.append(
            f'    {name} [label="{label}", shape=box, style="filled,rounded",'
            f' fillcolor="{GraphDisplay.FILL_NODE}",'
            f' color="{GraphDisplay.COLOR_NODE}", fontcolor="#1A1A1A",'
            f" penwidth={penwidth}];"
        )

    # Entry point edge
    if graph._entry_point:
      lines.append(f"    START -> {graph._entry_point} [penwidth=1.8];")

    # Dynamic Edges
    for edge in graph.edges:
      if edge.router is not None:
        if edge.display_paths:
          for label, target in edge.display_paths.items():
            lines.append(
                f'    {edge.start} -> {target} [label="  {label}  ",'
                ' style=dashed, color="#E65100", fontcolor="#E65100"];'
            )
        else:
          warnings.warn(
              f"Router '{edge.start}' has no display_paths defined.",
              stacklevel=2,
          )
      else:
        lines.append(f"    {edge.start} -> {edge.end};")

    lines.append("}")
    return "\n".join(lines)

  @staticmethod
  def _render_native(dot_src: str) -> str:
    """Attempts to compile DOT to SVG using the local Graphviz engine."""
    import graphviz

    # Check common Windows default install location if not in PATH
    if os.name == "nt" and not shutil.which("dot"):
      default_win_path = r"C:\Program Files\Graphviz\bin"
      if os.path.exists(default_win_path):
        os.environ["PATH"] += os.pathsep + default_win_path

    dot = graphviz.Source(dot_src)
    return dot.pipe(format="svg").decode("utf-8")

  @staticmethod
  def _open_in_browser_fallback(dot_src: str):
    """Fallback: opens a self-rendering WASM Graphviz page in the default browser."""
    import json

    dot_json = json.dumps(dot_src)
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Agent Graph (WASM View)</title>
    <style>
        body {{
            margin: 0;
            padding: 24px;
            background: #F8FAFC;
            font-family: system-ui, -apple-system, sans-serif;
            display: flex;
            flex-direction: column;
            align-items: center;
        }}
        #container {{
            background: #FFFFFF;
            border-radius: 12px;
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
            padding: 24px;
            max-width: 95vw;
            overflow: auto;
        }}
        .notice {{
            margin-bottom: 16px;
            font-size: 13px;
            color: #64748B;
        }}
    </style>
</head>
<body>
    <div class="notice">Rendered using WebAssembly Graphviz fallback</div>
    <div id="container">Generating graph...</div>

    <script type="module">
        import {{ instance }} from "https://cdn.jsdelivr.net/npm/@viz-js/viz@3.2.4/+esm";
        try {{
            const viz = await instance();
            const svg = viz.renderSVGElement({dot_json});
            const container = document.getElementById("container");
            container.innerHTML = "";
            container.appendChild(svg);
        }} catch (err) {{
            document.getElementById("container").innerHTML = "<pre style='color:red;'>Failed to render: " + err + "</pre>";
        }}
    </script>
</body>
</html>"""

    fd, path = tempfile.mkstemp(suffix=".html")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
      f.write(html_content)
    webbrowser.open(f"file://{path}")
    return path

  @staticmethod
  def render(graph, force_browser: bool = False):
        from IPython.display import HTML, display

        dot_src = GraphDisplay.to_dot(graph)

        # 1. Try native in-cell compilation only if not forced to browser
        if not force_browser:
            try:
                svg_str = GraphDisplay._render_native(dot_src)
                cell_html = f"""
                <div style="
                    width: 100%;
                    max-height: 85vh;
                    overflow: auto;
                    border: 1px solid #E2E8F0;
                    border-radius: 8px;
                    background: #FFFFFF;
                    padding: 16px;
                    box-sizing: border-box;
                    display: flex;
                    justify-content: center;
                ">
                    <div style="min-width: 600px; width: 100%; display: flex; justify-content: center;">
                        {svg_str}
                    </div>
                </div>
                """
                display(HTML(cell_html))
                return dot_src
            except Exception:
                pass

        # 2. Fallback / Forced: Open WASM viewer in default browser
        file_path = GraphDisplay._open_in_browser_fallback(dot_src)

        # 3. Dynamic in-cell card (changes message if user chose browser vs fallback)
        badge_text = "Manual Mode" if force_browser else "Fallback Mode"
        description = (
            "Graph opened in an external browser tab as requested."
            if force_browser
            else "Local Graphviz engine was not found on your system, so the interactive diagram was launched in your web browser instead."
        )

        guide_html = f"""
        <div style="
            border: 1px solid #CBD5E1;
            border-left: 5px solid #2563EB;
            border-radius: 8px;
            background: #F8FAFC;
            padding: 16px 20px;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            color: #1E293B;
            margin: 12px 0;
            line-height: 1.5;
        ">
            <div style="display: flex; align-items: center; justify-content: space-between;">
                <h4 style="margin: 0; font-size: 15px; color: #0F172A;">
                    🌐 Graph opened in your browser
                </h4>
                <span style="font-size: 11px; background: #E2E8F0; padding: 2px 8px; border-radius: 4px; color: #475569;">
                    {badge_text}
                </span>
            </div>
            <p style="margin: 8px 0 12px 0; font-size: 13px; color: #475569;">
                {description}
            </p>
            <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 6px; padding: 12px; font-size: 12px;">
                <strong style="color: #0F172A;">To render diagrams directly inside this notebook cell, install Graphviz:</strong>
                <ul style="margin: 6px 0 0 16px; padding: 0; color: #334155;">
                    <li><strong>Windows (PowerShell):</strong> <code style="background: #F1F5F9; color: #0F172A; padding: 2px 6px; border-radius: 4px;">winget install Graphviz.Graphviz</code></li>
                    <li><strong>macOS:</strong> <code style="background: #F1F5F9; color: #0F172A; padding: 2px 6px; border-radius: 4px;">brew install graphviz</code></li>
                    <li><strong>Linux / Debian / Ubuntu:</strong> <code style="background: #F1F5F9; color: #0F172A; padding: 2px 6px; border-radius: 4px;">sudo apt-get install graphviz</code></li>
                    <li><strong>Python package:</strong> <code style="background: #F1F5F9; color: #0F172A; padding: 2px 6px; border-radius: 4px;">pip install graphviz</code></li>
                </ul>
            </div>
        </div>
        """

        display(HTML(guide_html))
        return dot_src