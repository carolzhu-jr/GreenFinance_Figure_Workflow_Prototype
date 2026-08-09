
node-edge schema and richer diagram support

New file: profiles/node_edge_schema.json — a JSON Schema describing nodes and edges with optional shape, role, size overrides, waypoints, markers, and metadata.

pipeline_b/data/sample_graph.json — updated to show examples of roles, custom node size, arrow markers, dashed edge and metadata examples.

pipeline_b/generate_svg.py — updated to read the richer node/edge fields, render shapes (rect/circle/ellipse), dashed edges, arrow markers (via <defs>/marker), and emit named layers (layer-background, layer-edges, layer-nodes, layer-annotations). Metadata for nodes and edges is embedded in <desc> elements.

tests/test_node_edge_schema.py — validates sample_graph.json against the new schema, runs the generator, and checks that SVG contains node/edge metadata.

