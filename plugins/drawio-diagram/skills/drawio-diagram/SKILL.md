---
name: drawio-diagram
description: Use when producing or editing a draw.io / diagrams.net diagram — any `.drawio`, `.drawio.xml` or mxGraph XML file, or a request for a diagram where draw.io is named or is the working format ("構成図を作って", "フロー図を draw.io で", "ER図/シーケンス図/状態遷移図を描いて", "アーキテクチャ図", "この図のレイアウトを直して", "architecture diagram", "flowchart", "update the .drawio"). Applies layout rules that keep a diagram readable to a human: shapes, edges and labels never overlap, text fits inside its shape, categories are shown through colour and position, and the canvas grows to fit the content. Do NOT use when the user asks for another format — Mermaid, PlantUML, Graphviz, SVG or an image.
---

# draw.io Diagram Layout

Layout rules for diagrams a person can read without zooming or tracing a line with a finger.

The model here assumes a **layered block diagram**: box nodes, edges between them, one flow axis. ER tables, sequence lifelines and cyclic graphs relax specific rules — read `references/diagram-types.md` before drawing one.

## Non-negotiables

Conditions 1–4 hold **by construction**. You cannot see where draw.io's router draws a line, so never claim to have checked one.

1. Sibling shapes (same `parent`) are ≥40px apart on at least one axis. Nesting is exempt — a container, background rectangle or legend frame may hold shapes, which sit ≥20px inside its border.
2. No edge crosses a shape — every edge runs in a reserved channel (see Edges).
3. No two edges overlap — every edge gets its own port, every parallel pair its own waypoint offset.
4. Every label fits its shape, sized by the formula in Text; edge labels get an opaque background.
5. Categories are shown by colour **and** position whenever nodes split into two or more responsibilities, owners, environments or phases.
6. The canvas fits the layout — enlarge it, never compress the content.
7. Labels are noun phrases, ≤2 lines and ≤20 full-width characters; longer text goes in a note.

Workflow step 6 checks 1, 4, 6 and the ports behind 3. The rest is on the layout.

## Geometry

Snap every `x`, `y`, `width`, `height` to a **10px grid**. Coordinates are absolute, except inside a container where they are relative to the parent.

| Item | Value |
|------|-------|
| Canvas margin | 40px |
| Default node | 160 × 60 (small 120 × 40, wide label 200 × 60) |
| `gapX` between layers | 80px; **≥ edge-label width + 20** where a labelled edge runs |
| `gapY` between tracks | 40px |
| Between groups / swimlanes | ≥80px |
| Child inset from container border | ≥20px |

Pick one flow direction (left→right or top→bottom) and keep every primary edge going that way. Each node gets a **layer** (distance from the start, along the flow) and a **track** (position across it). *Lane* in this file always means a swimlane.

Node sizes vary, so derive coordinates from cumulative sums, never from one node width:

```
colW[i] = max width  of the nodes in layer i
rowH[j] = max height of the nodes in track j

x[i] = margin + Σ(k<i) (colW[k] + gapX)     every node in layer i gets x[i]
y[j] = margin + Σ(k<j) (rowH[k] + gapY)     every node in track j gets y[j]
```

This makes condition 1 structural at any node size. Two nodes sharing a layer *and* a track is a layout error — split the track.

## Edges

Base style: `edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;`.

**Reserve wiring channels.** The `gapX` strip between layers is where edges turn. Non-adjacent and backward edges run in a channel or around the outside of the block, never across the interior — this is what makes condition 2 hold.

- **Pin the ports.** `exitX/exitY/exitDx/exitDy` + `entryX/entryY`, so lines leave defined points rather than the shape centre. Left→right: `exitX=1;exitY=0.5;entryX=0;entryY=0.5`. The `Dx/Dy` pixel offsets are normally `0` — emit them anyway, draw.io does.
- **Fan out a shared side**: `exitY=0.25 / 0.5 / 0.75`. Two edges on one node sharing a port value is a defect the validator flags.
- **Parallel edges** between the same pair: waypoints offset ≥20px.
- **Backward edges**: explicit waypoints above the top track or below the bottom track, with the canvas extended to hold them.
- **Crossings** get `jumpStyle=arc;jumpSize=6;` on the hopping edge — but a crossing within one layer means the tracks are ordered wrongly; reorder instead.
- **Edge labels**: `labelBackgroundColor=#FFFFFF;`, 1–4 words, on a straight run rather than a corner, with `gapX` widened to fit. Needing labels everywhere means the layout wants swimlanes or a legend.

## Text inside shapes

Always `whiteSpace=wrap;html=1;` — without it draw.io renders the label on one line and lets it spill out.

At `fontSize=12` (the default), scaling both by `fontSize / 12` otherwise:

```
lineWidth ≈ (full-width chars × 12) + (half-width chars × 7)   ← the LONGEST line
width     ≥ lineWidth + 20      (10px padding each side)
height    ≥ lines × 18 + 16
```

Measure the longest line; draw.io's wrap does not split evenly, so averaging under-estimates.

- One idea per shape. Supplementary prose goes in a note (`shape=note;size=20;`) in the margin — outside the flow, ≥40px from any shape, grey and smaller.
- Text elements are shapes: they obey condition 1.
- Notations that are inherently multi-line (ER attribute lists) are exempt from condition 7 — see `references/diagram-types.md`.

## Grouping by colour and layout

Show a category **twice**: position groups the eye, colour confirms it. Put one category per track, layer or container — a swimlane or a dashed background rectangle (`verticalAlign=top`, light `fillColor`) with a group title, ≥80px from the next group.

Keep to **≤6 categories**, and never let colour be the only carrier — the title, position or shape must say it too, so the diagram survives greyscale and colour-blind readers. Add a legend when colour means something the labels do not spell out.

| Slot | Style | Use |
|------|-------|-----|
| 1 | `fillColor=#dae8fc;strokeColor=#6c8ebf` | primary (blue) |
| 2 | `fillColor=#d5e8d4;strokeColor=#82b366` | second (green) |
| 3 | `fillColor=#ffe6cc;strokeColor=#d79b00` | third (orange) |
| 4 | `fillColor=#e1d5e7;strokeColor=#9673a6` | fourth (purple) |
| 5 | `fillColor=#f8cecc;strokeColor=#b85450` | errors / alerts only (red) |
| 6 | `fillColor=#f5f5f5;strokeColor=#666666` | neutral / external |

## Canvas size

draw.io does **not** clip content past the page — it silently tiles the overflow onto extra pages, breaking the diagram in two without warning.

Lay out first, then fit the page to it: `pageWidth` / `pageHeight` on `<mxGraphModel>`, or `page="0"` for an unbounded canvas, with a 40px margin around everything including outside-routed waypoints. Never shrink shapes, fonts or gaps to fit a page.

**When the user fixed the drawing area** (a page size, a slide, an existing file's canvas) and the content does not fit at minimum spacing, **stop and confirm**: state the required size, then offer (1) enlarge / switch to landscape, (2) split into pages or sub-diagrams, (3) cut detail by collapsing a group into one node. Never silently overflow the page or resize a canvas the user specified.

## Working with an existing file

`.drawio` files are often **compressed**: if `<diagram>` holds a base64 blob instead of `<mxGraphModel>`, it is deflate-raw + base64 + URI-encoded. Decode before editing, and write back as plain XML — draw.io reads uncompressed files fine.

```bash
python3 -c "import base64,zlib,urllib.parse,sys;print(urllib.parse.unquote(zlib.decompress(base64.b64decode(sys.argv[1]),-15).decode()))" '<blob>'
```

Keep existing `mxCell` ids (edges reference nodes by id) and `<diagram id=... name=...>`, leave other pages alone, and read the current `pageWidth`/`pageHeight` — that is the fixed drawing area the rule above applies to.

## Workflow

0. **Existing file?** Read it, decompress if needed, record ids and page size.
1. **Collect** nodes, edges, and each node's category. Not a plain block diagram? Read `references/diagram-types.md` now.
2. **Assign** a flow direction, then a layer and track per node.
3. **Compute** `colW`/`rowH` and the cumulative coordinates; write the node table (`id, label, x, y, w, h, category, parent`).
4. **Assign edge ports and channels** — fan out shared sides, pick waypoints for backward and non-adjacent edges.
5. **Emit the XML**: containers, then nodes, then edges (z-order).
6. **Run the validator** and fix coordinates until it passes:
   ```bash
   python3 ${CLAUDE_PLUGIN_ROOT}/skills/drawio-diagram/scripts/validate_drawio.py <file.drawio>
   ```
7. **Report** what the diagram shows in one or two sentences, plus whatever the validator could not check.

## Example

Two layers in two groups, a fanned-out pair of forward edges, and a backward edge routed above the block.

```xml
<mxfile host="app.diagrams.net">
  <diagram id="flow-1" name="Flow">
    <mxGraphModel dx="1200" dy="800" grid="1" gridSize="10" page="1"
                  pageWidth="1100" pageHeight="850" math="0" shadow="0">
      <root>
        <mxCell id="0"/>
        <mxCell id="1" parent="0"/>

        <!-- containers first: drawn behind their contents -->
        <mxCell id="g1" value="Frontend" style="rounded=0;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;dashed=1;opacity=30;verticalAlign=top;fontStyle=1" vertex="1" parent="1">
          <mxGeometry x="40" y="60" width="240" height="260" as="geometry"/>
        </mxCell>
        <mxCell id="g2" value="Backend" style="rounded=0;whiteSpace=wrap;html=1;fillColor=#d5e8d4;strokeColor=#82b366;dashed=1;opacity=30;verticalAlign=top;fontStyle=1" vertex="1" parent="1">
          <mxGeometry x="360" y="60" width="240" height="260" as="geometry"/>
        </mxCell>

        <!-- layer 0 track 0 -->
        <mxCell id="n1" value="ログイン画面" style="rounded=0;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf" vertex="1" parent="1">
          <mxGeometry x="80" y="120" width="160" height="60" as="geometry"/>
        </mxCell>
        <!-- layer 1 track 0 : x = 80 + 160 + gapX(160, widened for the label) -->
        <mxCell id="n2" value="認証API" style="rounded=0;whiteSpace=wrap;html=1;fillColor=#d5e8d4;strokeColor=#82b366" vertex="1" parent="1">
          <mxGeometry x="400" y="120" width="160" height="60" as="geometry"/>
        </mxCell>
        <!-- layer 1 track 1 : y = 120 + 60 + gapY(40) -->
        <mxCell id="n3" value="セッション発行" style="rounded=0;whiteSpace=wrap;html=1;fillColor=#d5e8d4;strokeColor=#82b366" vertex="1" parent="1">
          <mxGeometry x="400" y="220" width="160" height="60" as="geometry"/>
        </mxCell>

        <mxCell id="e1" value="POST /login" style="edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;exitX=1;exitY=0.5;exitDx=0;exitDy=0;entryX=0;entryY=0.5;entryDx=0;entryDy=0;labelBackgroundColor=#FFFFFF;" edge="1" parent="1" source="n1" target="n2">
          <mxGeometry relative="1" as="geometry"/>
        </mxCell>
        <!-- second edge out of n1: a different exitY, never the same port -->
        <mxCell id="e2" style="edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;exitX=1;exitY=0.75;exitDx=0;exitDy=0;entryX=0;entryY=0.5;entryDx=0;entryDy=0;" edge="1" parent="1" source="n1" target="n3">
          <mxGeometry relative="1" as="geometry"/>
        </mxCell>
        <!-- backward edge: waypoints above the whole block, inside the margin -->
        <mxCell id="e3" value="expired" style="edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;exitX=0.5;exitY=0;exitDx=0;exitDy=0;entryX=0.5;entryY=0;entryDx=0;entryDy=0;labelBackgroundColor=#FFFFFF;jumpStyle=arc;jumpSize=6;" edge="1" parent="1" source="n3" target="n1">
          <mxGeometry relative="1" as="geometry">
            <Array as="points">
              <mxPoint x="480" y="20"/>
              <mxPoint x="160" y="20"/>
            </Array>
          </mxGeometry>
        </mxCell>
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>
```

## Anti-patterns

- Stacking nodes at the same coordinates and expecting draw.io to sort it out — there is no auto-layout on load.
- Omitting `whiteSpace=wrap;html=1;`, then wondering why the label runs past the border.
- Letting edges default to centre-to-centre routing, so five lines converge on one point.
- Renumbering ids while editing an existing file, detaching every edge.
- Sentences inside boxes: `ユーザーがログインボタンを押すと認証APIにリクエストを送信する` belongs in a note; the box says `ログイン画面`.
- Reporting "no overlaps, verified" without running the validator — the rendered routing is not visible to you.
