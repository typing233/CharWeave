import { useRef, useEffect, useState, useCallback, forwardRef, useImperativeHandle } from "react";
import * as d3 from "d3";

const TYPE_COLORS = {
  friend: "#27ae60",
  enemy: "#e74c3c",
  family: "#8e44ad",
  romantic: "#e91e63",
  mentor: "#f39c12",
  servant: "#795548",
  colleague: "#3498db",
  neutral: "#95a5a6",
};

const ForceGraph = forwardRef(function ForceGraph(
  { characters, relationships, activeTypes, onNodeClick },
  ref
) {
  const svgRef = useRef(null);
  const containerRef = useRef(null);
  const simulationRef = useRef(null);
  const [tooltip, setTooltip] = useState(null);

  useImperativeHandle(ref, () => ({
    getSvgElement: () => svgRef.current,
  }));

  useEffect(() => {
    if (!characters?.length || !svgRef.current || !containerRef.current) return;

    const container = containerRef.current;
    const width = container.clientWidth || 800;
    const height = 560;

    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove();
    svg.attr("width", width).attr("height", height);

    const g = svg.append("g");

    // Zoom behavior
    const zoom = d3.zoom()
      .scaleExtent([0.3, 4])
      .on("zoom", (event) => {
        g.attr("transform", event.transform);
      });
    svg.call(zoom);

    // Filter relationships by active types
    const filteredRels = relationships.filter(
      (r) => activeTypes.includes(r.type)
    );

    // Build nodes
    const nodes = characters.map((c) => ({
      id: c.name,
      mentions: c.mentions,
      ...c,
    }));

    const nodeMap = new Map(nodes.map((n) => [n.id, n]));

    // Build links (only include links whose both ends exist)
    const links = filteredRels
      .filter((r) => nodeMap.has(r.source) && nodeMap.has(r.target))
      .map((r) => ({
        source: r.source,
        target: r.target,
        weight: r.weight,
        type: r.type,
        confidence: r.confidence,
        direction: r.direction,
      }));

    // Force simulation
    const maxMentions = Math.max(...nodes.map((n) => n.mentions), 1);

    const simulation = d3
      .forceSimulation(nodes)
      .force(
        "link",
        d3.forceLink(links).id((d) => d.id).distance(120).strength(0.4)
      )
      .force("charge", d3.forceManyBody().strength(-300))
      .force("center", d3.forceCenter(width / 2, height / 2))
      .force("collide", d3.forceCollide().radius((d) => nodeRadius(d) + 10));

    simulationRef.current = simulation;

    function nodeRadius(d) {
      return 8 + Math.sqrt(d.mentions / maxMentions) * 20;
    }

    // Arrow markers for directed edges
    const defs = g.append("defs");
    Object.entries(TYPE_COLORS).forEach(([type, color]) => {
      defs
        .append("marker")
        .attr("id", `arrow-${type}`)
        .attr("viewBox", "0 -5 10 10")
        .attr("refX", 20)
        .attr("refY", 0)
        .attr("markerWidth", 6)
        .attr("markerHeight", 6)
        .attr("orient", "auto")
        .append("path")
        .attr("d", "M0,-5L10,0L0,5")
        .attr("fill", color);
    });

    // Draw links
    const link = g
      .append("g")
      .attr("class", "links")
      .selectAll("line")
      .data(links)
      .join("line")
      .attr("stroke", (d) => TYPE_COLORS[d.type] || "#999")
      .attr("stroke-width", (d) => Math.max(1.5, Math.log(d.weight + 1) * 1.5))
      .attr("stroke-opacity", 0.7)
      .attr("marker-end", (d) =>
        d.direction !== "bidirectional" ? `url(#arrow-${d.type})` : null
      );

    // Link hover for tooltip
    link
      .on("mouseenter", (event, d) => {
        setTooltip({
          x: event.offsetX,
          y: event.offsetY,
          content: `${d.source.id || d.source} — ${d.target.id || d.target}\n类型: ${d.type} | 权重: ${d.weight}\n置信度: ${(d.confidence * 100).toFixed(0)}%`,
        });
      })
      .on("mouseleave", () => setTooltip(null));

    // Draw nodes
    const node = g
      .append("g")
      .attr("class", "nodes")
      .selectAll("g")
      .data(nodes)
      .join("g")
      .attr("cursor", "pointer");

    node
      .append("circle")
      .attr("r", (d) => nodeRadius(d))
      .attr("fill", "#5b8def")
      .attr("stroke", "#fff")
      .attr("stroke-width", 2)
      .on("mouseenter", (event, d) => {
        d3.select(event.currentTarget).attr("fill", "#3a6fd8");
        setTooltip({
          x: event.offsetX,
          y: event.offsetY,
          content: `${d.name}\n提及次数: ${d.mentions}`,
        });
      })
      .on("mouseleave", (event) => {
        d3.select(event.currentTarget).attr("fill", "#5b8def");
        setTooltip(null);
      })
      .on("click", (event, d) => {
        event.stopPropagation();
        if (onNodeClick) onNodeClick(d);
      });

    // Node labels
    node
      .append("text")
      .text((d) => d.name)
      .attr("text-anchor", "middle")
      .attr("dy", (d) => nodeRadius(d) + 14)
      .attr("font-size", "11px")
      .attr("fill", "#333")
      .attr("pointer-events", "none");

    // Drag behavior
    const drag = d3
      .drag()
      .on("start", (event, d) => {
        if (!event.active) simulation.alphaTarget(0.3).restart();
        d.fx = d.x;
        d.fy = d.y;
      })
      .on("drag", (event, d) => {
        d.fx = event.x;
        d.fy = event.y;
      })
      .on("end", (event, d) => {
        if (!event.active) simulation.alphaTarget(0);
        d.fx = null;
        d.fy = null;
      });

    node.call(drag);

    // Tick
    simulation.on("tick", () => {
      link
        .attr("x1", (d) => d.source.x)
        .attr("y1", (d) => d.source.y)
        .attr("x2", (d) => d.target.x)
        .attr("y2", (d) => d.target.y);

      node.attr("transform", (d) => `translate(${d.x},${d.y})`);
    });

    return () => {
      simulation.stop();
    };
  }, [characters, relationships, activeTypes, onNodeClick]);

  return (
    <div ref={containerRef} className="force-graph-container">
      <svg ref={svgRef} />
      {tooltip && (
        <div
          className="graph-tooltip"
          style={{ left: tooltip.x + 12, top: tooltip.y - 10 }}
        >
          {tooltip.content.split("\n").map((line, i) => (
            <div key={i}>{line}</div>
          ))}
        </div>
      )}
    </div>
  );
});

export { TYPE_COLORS };
export default ForceGraph;
