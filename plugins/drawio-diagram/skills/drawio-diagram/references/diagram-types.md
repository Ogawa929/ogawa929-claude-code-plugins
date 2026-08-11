# Notation-specific rules

The layout model in `SKILL.md` assumes a layered block diagram: box nodes, edges between them, one flow axis. The notations below break that assumption. Each entry lists the layout axis, which non-negotiables are relaxed, and the draw.io styles to use. Everything not listed here still applies — in particular the 10px grid, colour+position grouping, canvas sizing, and concise text.

## ER diagram

**Layout axis** — one axis along the dependency direction: referenced (parent) tables on the left, referencing (child) tables on the right. Junction tables sit between the two they join. Track order: put tables that share a foreign key adjacent so relation edges stay short.

**Relaxed**
- *Condition 1 (40px gap)* does not apply to attribute rows inside a table — they stack with zero gap by design. It still applies between whole tables (≥40px, ≥80px between subject areas).
- *Condition 7 (≤2 lines)* does not apply to the attribute list. The **table title** still obeys it.

**Styles**

```
table:  swimlane;childLayout=stackLayout;horizontal=1;startSize=30;horizontalStack=0;
        resizeParent=1;resizeParentMax=0;resizeLast=0;collapsible=1;marginBottom=0;
        whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;
row:    shape=partialRectangle;top=0;left=0;bottom=0;right=0;align=left;
        verticalAlign=middle;spacingLeft=6;whiteSpace=wrap;html=1;fillColor=none;
```

Row height is 30 by default; table height = `startSize + rows × 30`. Rows are children of the table cell with relative `y` — `x=0`, `width` = table width.

**Relation edges** — crow's foot, attached to the row cells rather than the table when the FK column matters:

| Cardinality | Style fragment |
|-------------|----------------|
| 1 : N | `startArrow=ERone;startFill=0;endArrow=ERmany;endFill=0;` |
| 1 : 1 | `startArrow=ERone;startFill=0;endArrow=ERone;endFill=0;` |
| 0..1 : N | `startArrow=ERzeroToOne;startFill=0;endArrow=ERmany;endFill=0;` |
| N : M | `startArrow=ERmany;startFill=0;endArrow=ERmany;endFill=0;` |

Add `edgeStyle=entityRelationEdgeStyle;` instead of `orthogonalEdgeStyle` for the classic ER routing.

## Sequence diagram

**Layout axis** — two axes, and that is intentional: **vertical = time**, **horizontal = actor**. The single-axis rule in `SKILL.md` does not apply. Actors are evenly spaced across the top (`gapX` ≥ 120 so message labels fit); messages are ordered top to bottom with ≥40px between consecutive arrows.

**Relaxed**
- *Condition 2 (no edge crosses a shape)* does not apply to messages crossing lifelines — a message passing over an uninvolved lifeline is normal notation. It **does** still apply to messages crossing an *activation bar* or a note: route those around, or widen the actor spacing.
- *Condition 1* does not apply between a lifeline and its own activation bars (they overlap by design), nor between an actor head and its lifeline.

**Styles**

```
lifeline:    shape=umlLifeline;perimeter=lifelinePerimeter;whiteSpace=wrap;html=1;
             container=1;collapsible=0;recursiveResize=0;outlineConnect=0;size=40;
activation:  html=1;points=[];perimeter=orthogonalPerimeter;fillColor=#ffffff;
             strokeColor=#000000;   (width 10, child of the lifeline)
message:     html=1;verticalAlign=bottom;endArrow=block;
reply:       html=1;verticalAlign=bottom;endArrow=open;endSize=8;dashed=1;
self-call:   edgeStyle=orthogonalEdgeStyle;html=1;align=left;spacingLeft=4;
             endArrow=block;rounded=0;   + waypoints out and back, 30px wide
frame:       shape=umlFrame;whiteSpace=wrap;html=1;width=60;height=30;  (alt / loop / opt)
```

Lifeline `height` must reach below the last message. Extend it and the page together rather than compressing the vertical spacing.

## State machine / activity diagram

**Layout axis** — one axis, but the graph is **cyclic**, so `layer = distance from the start` is undefined for nodes on a cycle. Approximate it:

1. Run a BFS from the initial state; the BFS depth is the layer.
2. Any edge whose target layer ≤ source layer is a **back edge** — mark it, and route it outside the block per the backward-edge rule in `SKILL.md`.
3. Self-transitions loop on one side: `exitX=1;exitY=0.25;entryX=1;entryY=0.75;` with two waypoints 40px outside the shape. Never loop on the side an incoming edge already uses.

**Styles**

```
state:     rounded=1;arcSize=20;whiteSpace=wrap;html=1;
initial:   ellipse;fillColor=#000000;strokeColor=none;   (30 × 30)
final:     ellipse;shape=endState;fillColor=#000000;strokeColor=#000000;  (30 × 30)
decision:  rhombus;whiteSpace=wrap;html=1;   (80 × 80, label the outgoing edges not the shape)
```

Guard conditions go on the edge as `[condition]` with `labelBackgroundColor=#FFFFFF;`, kept to ≤4 words.

## Network diagram

**Layout axis** — hub-and-spoke and mesh topologies have no single flow direction. Two workable choices:

- **Tiered** (preferred, and the one the `SKILL.md` model fits): internet → edge → core → access → hosts, one tier per track. Treat each tier as a category for the colour+position rule.
- **Radial**: only when the topology is genuinely a star. Place the hub at the centre and spokes on a circle, `x = cx + r·cos θ`, `y = cy + r·sin θ`, snapped to the 10px grid, with ≥40px between neighbouring spoke bounding boxes (so `r ≥ (n × (nodeWidth + 40)) / 2π`).

**Relaxed** — nothing. Condition 2 in particular still holds: in a mesh, use `jumpStyle=arc` for the crossings that tiering cannot remove.

**Styles** — the network stencils carry their own labels below the icon, so shape width is the *icon* width, not the text width:

```
sketch=0;html=1;outlineConnect=0;fontColor=#232F3E;verticalLabelPosition=bottom;
verticalAlign=top;align=center;shape=mxgraph.networks.<name>;fillColor=#666666;
```

Common `<name>` values: `router`, `switch`, `firewall`, `server`, `cloud`, `pc`, `load_balancer`. Because the label sits **below** the shape, reserve `gapY ≥ 60` so labels never touch the next tier — that label is a shape for the purposes of condition 1.

## Class diagram

**Layout axis** — one axis along the inheritance direction, superclasses above subclasses (top→bottom). Composition and association edges run horizontally between tracks.

**Relaxed** — same as ER: attribute and method rows stack with zero gap and are exempt from the ≤2-line rule; the class name is not.

**Styles** — the ER `swimlane` + `partialRectangle` pair works, with a divider between attributes and methods:

```
divider row: line;strokeWidth=1;fillColor=none;align=left;verticalAlign=middle;
             spacingTop=-1;spacingLeft=3;spacingRight=3;rotatable=0;labelPosition=right;
             points=[];portConstraint=eastwest;   (height 8)
inheritance: endArrow=block;endSize=16;endFill=0;html=1;
composition: endArrow=diamondThin;endFill=1;endSize=14;html=1;
aggregation: endArrow=diamondThin;endFill=0;endSize=14;html=1;
```

## Anything else

If the notation is not listed, ask one question before drawing: **does it reduce to boxes connected by edges along one axis?** If yes, use `SKILL.md` unchanged. If no, say which non-negotiable the notation breaks and why, propose the relaxation, and confirm it with the user before drawing.
