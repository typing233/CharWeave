import { TYPE_COLORS } from "./ForceGraph";

function GraphLegend() {
  return (
    <div className="graph-legend">
      <div className="legend-title">图例</div>
      <div className="legend-items">
        {Object.entries(TYPE_COLORS).map(([type, color]) => (
          <div key={type} className="legend-item">
            <span className="legend-line" style={{ background: color }} />
            <span>{type}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

export default GraphLegend;
