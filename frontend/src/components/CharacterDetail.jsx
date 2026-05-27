import { TYPE_COLORS } from "./ForceGraph";

function CharacterDetail({ character, relationships, onClose }) {
  const related = relationships.filter(
    (r) => r.source === character.name || r.target === character.name
  );

  return (
    <aside className="character-detail">
      <div className="detail-header">
        <h3>{character.name}</h3>
        <button className="detail-close" onClick={onClose}>×</button>
      </div>
      <div className="detail-mentions">提及次数: {character.mentions}</div>
      <div className="detail-relations">
        <h4>关系 ({related.length})</h4>
        <ul className="detail-list">
          {related.map((rel, i) => {
            const other =
              rel.source === character.name ? rel.target : rel.source;
            return (
              <li key={i} className="detail-rel-item">
                <span
                  className="detail-type-badge"
                  style={{ background: TYPE_COLORS[rel.type] || "#999" }}
                >
                  {rel.type}
                </span>
                <span className="detail-other-name">{other}</span>
                <span className="detail-confidence">
                  {(rel.confidence * 100).toFixed(0)}%
                </span>
                {rel.passages && rel.passages.length > 0 && (
                  <blockquote className="detail-passage">
                    {rel.passages[0].slice(0, 150)}...
                  </blockquote>
                )}
              </li>
            );
          })}
        </ul>
      </div>
    </aside>
  );
}

export default CharacterDetail;
