import { TYPE_COLORS } from "./ForceGraph";

function GraphFilters({ activeTypes, onToggle }) {
  const allActive = activeTypes.length === Object.keys(TYPE_COLORS).length;

  return (
    <div className="graph-filters">
      <div className="filter-header">
        <span>关系类型筛选</span>
        <button
          className="filter-toggle-all"
          onClick={() => onToggle(allActive ? "none" : "all")}
        >
          {allActive ? "全部隐藏" : "全部显示"}
        </button>
      </div>
      <div className="filter-list">
        {Object.entries(TYPE_COLORS).map(([type, color]) => (
          <label key={type} className="filter-item">
            <input
              type="checkbox"
              checked={activeTypes.includes(type)}
              onChange={() => onToggle(type)}
            />
            <span className="filter-swatch" style={{ background: color }} />
            <span className="filter-label">{type}</span>
          </label>
        ))}
      </div>
    </div>
  );
}

export default GraphFilters;
