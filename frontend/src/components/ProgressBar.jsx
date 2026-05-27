function ProgressBar({ progress, stage }) {
  return (
    <div className="progress-container">
      <div className="progress-bar-track">
        <div
          className="progress-bar-fill"
          style={{ width: `${Math.min(progress, 100)}%` }}
        />
      </div>
      <div className="progress-info">
        <span className="progress-stage">{stage}</span>
        <span className="progress-pct">{progress}%</span>
      </div>
    </div>
  );
}

export default ProgressBar;
