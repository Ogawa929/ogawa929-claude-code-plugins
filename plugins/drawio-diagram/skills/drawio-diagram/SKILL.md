---
name: drawio-diagram
description: Use when producing or editing a draw.io / diagrams.net diagram — any `.drawio`, `.drawio.xml` or mxGraph XML file, or a request for a diagram where draw.io is named or is the working format ("構成図を作って", "フロー図を draw.io で", "ER図/シーケンス図/状態遷移図を描いて", "アーキテクチャ図", "この図のレイアウトを直して", "architecture diagram", "flowchart", "update the .drawio"). Applies layout rules that keep a diagram readable to a human: shapes, edges and labels never overlap, text fits inside its shape, categories are shown through colour and position, and the canvas grows to fit the content. Do NOT use when the user asks for another format — Mermaid, PlantUML, Graphviz, SVG or an image.
---

# draw.io Diagram Layout

Rules that apply to every diagram type — flow, architecture, ER, sequence, state, network. They are about **layout and legibility**, not about a specific notation.

The layout model in this file assumes a **layered block diagram**: nodes are boxes, edges connect them, and the graph reduces to a single flow axis. Notations that break that assumption — ER tables, sequence lifelines, cyclic graphs — relax specific rules; read `references/diagram-types.md` before drawing one.

A diagram is finished when a person can read it without zooming, tracing a line with a finger, or asking which box a label belongs to.

## Non-negotiables

Every diagram must satisfy all seven. Conditions 1–4 are **constructive**: they are satisfied by how the layout is built, not by inspecting the result afterwards. Do not claim to have "checked" a routing you cannot see.

1. **No two sibling shapes overlap.** Any two shapes with the same `parent` are separated by ≥40px on at least one axis. *Excluded: a container and its children, a background rectangle and the shapes inside it, a legend frame and its items — these nest by design. Children sit ≥20px inside the container border.*
2. **No edge crosses a shape** — guaranteed by routing every edge inside a reserved wiring channel (see Edges), never by eyeballing the rendered line.
3. **Edges do not overlap each other** — guaranteed by giving every edge on a shared side its own port and every parallel edge its own offset waypoint.
4. **Every label fits inside its shape**, sized by the formula in Text, with edge labels given an opaque background.
5. **Groups are visible** through both colour and position whenever nodes split into two or more responsibilities, owners, environments, or phases.
6. **The canvas is large enough** for the layout — enlarge it rather than compressing the content.
7. **Text is concise** — shape labels are noun phrases of ≤2 lines and ≤20 full-width characters; anything longer goes in a note.

Run the validator (see Workflow) before reporting the work as done. It checks what is mechanically checkable: 1, 4, 6, and the port rule behind 3.

## Geometry

Work on a **10px grid**: every `x`, `y`, `width`, `height` in `mxGeometry` is a multiple of 10. Coordinates are absolute unless the shape is inside a container (then they are relative to the parent).

| Item | Value |
|------|-------|
| Grid | 10px — snap everything |
| Canvas margin | 40px from the top-left origin |
| Default node | 160 × 60 (small: 120 × 40, wide label: 200 × 60) |
| `gapX` (between layers) | 80px default; **≥ edge-label width + 20** when a labelled edge runs through that channel |
| `gapY` (between tracks) | 40px |
| Between groups / swimlanes | ≥80px |
| Child inset from container border | ≥20px |

**Lay out on one axis.** Pick a single flow direction — left→right, or top→bottom — and keep every primary edge going that way. Give each node:

- a **layer** — its distance from the start node, along the flow;
- a **track** — its position across the flow.

("Track" is the across-flow index. "Lane" in this file always means a swimlane, i.e. a container.)

Node sizes vary, so compute coordinates from **cumulative sums of the actual sizes**, never from a single node width:

```
colW[i] = max width  of the nodes in layer i
rowH[j] = max height of the nodes in track j

x[i] = margin + Σ(k<i) (colW[k] + gapX)
y[j] = margin + Σ(k<j) (rowH[k] + gapY)
```

Every node in layer `i` gets `x = x[i]`; every node in track `j` gets `y = y[j]`. This makes condition 1 structural: distinct layers are ≥gapX apart and distinct tracks ≥gapY apart, whatever the node sizes. Nodes sharing both a layer and a track are a layout error — split the track.

Consistent alignment does more for readability than any styling.

## Edges

Base style: `edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;`.

**Reserve wiring channels.** The `gapX` strip between two layers is where edges turn. Every edge that is not between adjacent layers, and every backward edge, is routed through a channel or around the outside of the block — never across the interior where nodes live. This is what makes condition 2 hold by construction.

- **Pin the sides.** Set `exitX/exitY/exitDx/exitDy` and `entryX/entryY` so lines leave and arrive at defined ports instead of the shape centre. In a left→right flow: `exitX=1;exitY=0.5;entryX=0;entryY=0.5`. `exitDx`/`exitDy` are pixel offsets on top of the relative port and are normally `0` — always emit them, draw.io writes them itself.
- **Fan out multiple edges on the same side.** Three edges leaving one node use `exitY=0.25 / 0.5 / 0.75`, never the same point. Two edges sharing a node *and* a port value is a defect the validator flags.
- **Parallel edges between the same pair** get waypoints offset by ≥20px, so they read as two lines.
- **Backward / feedback edges** are routed outside the block — above the top track or below the bottom track — via explicit waypoints, and the canvas is extended to hold them. Never through the middle.
- **Unavoidable crossings** get `jumpStyle=arc;jumpSize=6;` on the edge that hops. A crossing is *unavoidable* only when it joins different layers; two edges crossing within one layer means the tracks are ordered wrongly — reorder them instead. (Jumps render on orthogonal/segment edges and are also subject to the file's Line Jumps setting.)
- **Edge labels** carry `labelBackgroundColor=#FFFFFF;` and sit on a straight run of the line, not on a corner. Keep them to 1–4 words, and widen `gapX` to fit them. When too many edges need labels, the layout is wrong — introduce swimlanes or a legend instead.

## Text inside shapes

Always set `whiteSpace=wrap;html=1;` — without it draw.io renders labels on one line and lets them spill out of the shape.

Size the shape to the text. At `fontSize=12` (draw.io's default):

```
lineWidth ≈ (full-width chars × 12) + (half-width chars × 7)   ← of the LONGEST line
width     ≥ lineWidth + 20        (10px padding each side)
height    ≥ lines × 18 + 16
```

Scale both by `fontSize / 12` when the shape uses a different size. Measure the longest line, not the total divided by the line count — draw.io's word wrap does not split lines evenly, and averaging under-estimates the width.

- Keep labels to **≤2 lines, ≤20 full-width characters**. Longer text belongs in a note shape, not in the box. (Exception: notations whose content is inherently multi-line, such as ER attribute lists — see `references/diagram-types.md`.)
- One idea per shape. Never pack a sentence into a node.
- Use a **note shape** (`shape=note;size=20;`) or a separate text element for supplementary explanation, placed in the margin — outside the flow, ≥40px from any shape, and visually subordinate (grey text, smaller font).
- Text elements are shapes too: they obey condition 1.

## Grouping by colour and layout

When nodes split into two or more responsibilities, owners, environments, or phases, **show it twice**: with position and with colour. Position groups the eye, colour confirms it.

- **Position:** put one category per track, layer, or container. Use a swimlane or a background rectangle (`fillColor` light, `strokeColor` dashed, `verticalAlign=top`) with a group title, and keep ≥80px between groups.
- **Colour:** one fill per category, applied consistently, with a dark stroke of the same hue and near-black text. Keep to **≤6 categories**; beyond that, split the diagram.
- **Never encode meaning in colour alone** — the group title, the position, or a shape difference must carry it too, so the diagram survives greyscale printing and colour-blind readers.
- Add a **legend** in a corner when colour carries meaning that the labels do not spell out.

A workable default palette (draw.io's built-in swatches, light fill / dark stroke). Assign one row per category and record the mapping in the legend:

| Slot | Style | Typical use |
|------|-------|-------------|
| 1 | `fillColor=#dae8fc;strokeColor=#6c8ebf` | primary category (blue) |
| 2 | `fillColor=#d5e8d4;strokeColor=#82b366` | second category (green) |
| 3 | `fillColor=#ffe6cc;strokeColor=#d79b00` | third category (orange) |
| 4 | `fillColor=#e1d5e7;strokeColor=#9673a6` | fourth category (purple) |
| 5 | `fillColor=#f8cecc;strokeColor=#b85450` | errors / alerts only (red) |
| 6 | `fillColor=#f5f5f5;strokeColor=#666666` | neutral / external / out of scope |

## Canvas size

The canvas serves the layout, not the other way round. draw.io does **not** clip content that exceeds the page — it silently tiles it across extra pages, so an overflowing diagram breaks in two without warning.

- **Content first.** Compute the layout, then set the page to fit it: `pageWidth` / `pageHeight` on `<mxGraphModel>`, or `page="0"` for an unbounded canvas. Leave a 40px margin on all four sides, including around waypoints of outside-routed edges.
- **Never shrink shapes, fonts, or gaps to fit a page.** If the content does not fit, the page is too small.
- **When the user has fixed the drawing area** (a given page size, a slide, an existing file's canvas) and the content does not fit at the minimum spacing: **stop and confirm before changing it.** State the required size, then offer concrete options and let the user pick:
  1. enlarge the canvas / switch to landscape,
  2. split into multiple pages or sub-diagrams,
  3. cut detail (collapse a group into one node).

  Do not silently overflow the page, and do not silently resize a canvas the user specified.

## Working with an existing file

`.drawio` files are often **compressed**: if the content of `<diagram>` is not `<mxGraphModel>` but a base64 blob, it is deflate-raw + base64 + URI-encoded. Decode it before editing, and write the file back as **plain XML** — draw.io reads uncompressed files fine.

```bash
python3 -c "import base64,zlib,urllib.parse,sys;print(urllib.parse.unquote(zlib.decompress(base64.b64decode(sys.argv[1]),-15).decode()))" '<blob>'
```

When editing rather than creating:

- **Keep existing `mxCell` ids.** Edges reference nodes by id; renumbering them silently detaches the diagram.
- **Preserve `<diagram id=... name=...>`** and never touch pages other than the one being edited.
- Read the current `pageWidth` / `pageHeight` before laying out — that is the fixed drawing area the confirmation rule above applies to.

## Workflow

0. **If a file already exists**, read it, decompress if needed, and record the existing ids and page size.
1. **Collect the elements** — nodes, edges, and which category each node belongs to. If the notation is not a plain block diagram, read `references/diagram-types.md` now.
2. **Choose the flow direction and grouping axis**, then assign every node a layer and a track.
3. **Compute `colW` / `rowH` and the cumulative coordinates** on the 10px grid; write out the node table (`id, label, x, y, w, h, category, parent`).
4. **Assign edge ports and channels**: fan out shared sides, pick waypoints for backward and non-adjacent edges.
5. **Emit the XML**: containers first (z-order), then nodes, then edges.
6. **Run the validator** and fix the coordinates until it passes:
   ```bash
   python3 ${CLAUDE_PLUGIN_ROOT}/skills/drawio-diagram/scripts/validate_drawio.py <file.drawio>
   ```
7. **Report** what the diagram shows in one or two sentences, plus anything the validator could not check.

## Minimal example

Two layers, a group container, a labelled forward edge, a backward edge routed above the block, and a note. Note the negative `y` on the backward edge's waypoints — the page origin is shifted to keep the 40px margin.

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

        <!-- layer 0 / track 0 : x[0]=80, y[0]=120 -->
        <mxCell id="n1" value="ログイン画面" style="rounded=0;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf" vertex="1" parent="1">
          <mxGeometry x="80" y="120" width="160" height="60" as="geometry"/>
        </mxCell>
        <!-- layer 1 / track 0 : x[1] = 80 + 160 + gapX(120, widened for the label) -->
        <mxCell id="n2" value="認証API" style="rounded=0;whiteSpace=wrap;html=1;fillColor=#d5e8d4;strokeColor=#82b366" vertex="1" parent="1">
          <mxGeometry x="400" y="120" width="160" height="60" as="geometry"/>
        </mxCell>
        <!-- layer 1 / track 1 : y[1] = 120 + 60 + gapY(40) -->
        <mxCell id="n3" value="セッション発行" style="rounded=0;whiteSpace=wrap;html=1;fillColor=#d5e8d4;strokeColor=#82b366" vertex="1" parent="1">
          <mxGeometry x="400" y="220" width="160" height="60" as="geometry"/>
        </mxCell>

        <mxCell id="note1" value="失効時は再ログインへ戻る" style="shape=note;size=20;whiteSpace=wrap;html=1;fillColor=#f5f5f5;strokeColor=#666666;fontColor=#666666;fontSize=10;align=left" vertex="1" parent="1">
          <mxGeometry x="640" y="220" width="160" height="60" as="geometry"/>
        </mxCell>

        <!-- forward edge: ports pinned, label with opaque background -->
        <mxCell id="e1" value="POST /login" style="edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;exitX=1;exitY=0.5;exitDx=0;exitDy=0;entryX=0;entryY=0.5;entryDx=0;entryDy=0;labelBackgroundColor=#FFFFFF;" edge="1" parent="1" source="n1" target="n2">
          <mxGeometry relative="1" as="geometry"/>
        </mxCell>

        <!-- second edge out of n1: a different exitY, never the same port -->
        <mxCell id="e2" style="edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;exitX=1;exitY=0.75;exitDx=0;exitDy=0;entryX=0;entryY=0.5;entryDx=0;entryDy=0;" edge="1" parent="1" source="n1" target="n3">
          <mxGeometry relative="1" as="geometry"/>
        </mxCell>

        <!-- backward edge: routed above the whole block via explicit waypoints -->
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

- Dropping every node at `x=0` or stacking them at the same coordinates and expecting draw.io to sort it out — there is no auto-layout on load.
- Omitting `whiteSpace=wrap;html=1;`, then wondering why the label runs past the border.
- Letting edges default to centre-to-centre routing, so five lines converge on one point.
- Shrinking gaps to 10px to make everything fit a fixed page instead of asking about the page.
- Renumbering ids while editing an existing file, detaching every edge.
- A rainbow of fills with no legend and no positional grouping — colour that means nothing costs attention.
- Sentences inside boxes: `ユーザーがログインボタンを押すと認証APIにリクエストを送信する` belongs in a note; the box says `ログイン画面`.
- Reporting "no overlaps, verified" without running the validator — the rendered routing is not visible to you.
