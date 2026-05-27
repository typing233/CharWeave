import { useState, useRef, useCallback } from "react";
import SearchPanel from "./components/SearchPanel";
import ForceGraph, { TYPE_COLORS } from "./components/ForceGraph";
import GraphFilters from "./components/GraphFilters";
import GraphLegend from "./components/GraphLegend";
import GraphExport from "./components/GraphExport";
import CharacterDetail from "./components/CharacterDetail";
import ProgressBar from "./components/ProgressBar";
import "./App.css";

const API_BASE = "http://localhost:8000";
const ALL_TYPES = Object.keys(TYPE_COLORS);

function App() {
  const [results, setResults] = useState([]);
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [progress, setProgress] = useState({ pct: 0, stage: "" });
  const [activeTypes, setActiveTypes] = useState(ALL_TYPES);
  const [selectedChar, setSelectedChar] = useState(null);
  const graphRef = useRef(null);

  const handleSearch = async (query, searchType) => {
    setError("");
    setLoading(true);
    try {
      const resp = await fetch(`${API_BASE}/api/search`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query, search_type: searchType }),
      });
      const data = await resp.json();
      setResults(data.results || []);
    } catch (e) {
      setError("搜索失败: " + e.message);
    } finally {
      setLoading(false);
    }
  };

  const handleAnalyze = async (book) => {
    if (!book.ia_id) {
      setError("该书籍无 Internet Archive 资源，无法获取全文。");
      return;
    }
    setError("");
    setLoading(true);
    setAnalysis(null);
    setSelectedChar(null);
    setProgress({ pct: 0, stage: "正在启动分析..." });

    try {
      // Start async analysis
      const startResp = await fetch(`${API_BASE}/api/analyze/start`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ia_id: book.ia_id, title: book.title }),
      });
      const { job_id } = await startResp.json();

      // Poll for progress
      let result = null;
      while (true) {
        await new Promise((r) => setTimeout(r, 1500));
        const progResp = await fetch(`${API_BASE}/api/analyze/progress/${job_id}`);
        const job = await progResp.json();

        setProgress({ pct: job.progress, stage: job.stage });

        if (job.status === "complete") {
          result = job.result;
          break;
        }
        if (job.status === "error") {
          throw new Error(job.stage);
        }
      }

      setAnalysis(result);
    } catch (e) {
      setError("分析失败: " + e.message);
    } finally {
      setLoading(false);
    }
  };

  const handleFilterToggle = useCallback((type) => {
    if (type === "all") {
      setActiveTypes(ALL_TYPES);
    } else if (type === "none") {
      setActiveTypes([]);
    } else {
      setActiveTypes((prev) =>
        prev.includes(type) ? prev.filter((t) => t !== type) : [...prev, type]
      );
    }
  }, []);

  const handleNodeClick = useCallback(
    (node) => {
      const char = analysis?.characters?.find((c) => c.name === node.name);
      if (char) setSelectedChar(char);
    },
    [analysis]
  );

  return (
    <div className="app">
      <header className="app-header">
        <h1>CharWeave</h1>
        <p>书籍人物关系图谱自动生成工具</p>
      </header>

      <SearchPanel onSearch={handleSearch} />

      {error && <div className="error-msg">{error}</div>}

      {loading && (
        <div className="loading-section">
          <ProgressBar progress={progress.pct} stage={progress.stage} />
        </div>
      )}

      {results.length > 0 && !analysis && !loading && (
        <div className="results">
          <h2>搜索结果</h2>
          <ul className="book-list">
            {results.map((book, idx) => (
              <li key={idx} className="book-item">
                <div className="book-info">
                  <strong>{book.title}</strong>
                  <span className="book-meta">
                    {book.authors?.join(", ")} {book.year && `(${book.year})`}
                    {book.has_text && <span className="text-badge">全文可用</span>}
                  </span>
                </div>
                <button
                  onClick={() => handleAnalyze(book)}
                  disabled={!book.has_text || loading}
                  className="analyze-btn"
                >
                  {book.has_text ? "分析人物关系" : book.ia_id ? "无文本文件" : "无资源"}
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}

      {analysis && (
        <div className="analysis">
          <div className="analysis-header">
            <h2>《{analysis.title}》人物关系图</h2>
            <button className="back-btn" onClick={() => { setAnalysis(null); setSelectedChar(null); }}>
              返回搜索结果
            </button>
          </div>

          <div className="characters">
            <h3>提取到的主要人物 ({analysis.characters.length})</h3>
            <div className="char-tags">
              {analysis.characters.map((c, i) => (
                <span
                  key={i}
                  className={`char-tag ${selectedChar?.name === c.name ? "char-tag-active" : ""}`}
                  onClick={() => setSelectedChar(c)}
                >
                  {c.name}
                  <span className="char-mentions">{c.mentions}</span>
                </span>
              ))}
            </div>
          </div>

          <div className="graph-section">
            <div className="graph-sidebar">
              <GraphFilters activeTypes={activeTypes} onToggle={handleFilterToggle} />
              <GraphLegend />
            </div>

            <div className="graph-main">
              <ForceGraph
                ref={graphRef}
                characters={analysis.characters}
                relationships={analysis.relationships}
                activeTypes={activeTypes}
                onNodeClick={handleNodeClick}
              />
              <GraphExport graphRef={graphRef} mermaidCode={analysis.mermaid} />
            </div>

            {selectedChar && (
              <CharacterDetail
                character={selectedChar}
                relationships={analysis.relationships}
                onClose={() => setSelectedChar(null)}
              />
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
