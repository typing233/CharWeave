import { useState } from "react";
import SearchPanel from "./components/SearchPanel";
import MermaidChart from "./components/MermaidChart";
import "./App.css";

const API_BASE = "http://localhost:8000";

function App() {
  const [results, setResults] = useState([]);
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

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
    try {
      const resp = await fetch(`${API_BASE}/api/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ia_id: book.ia_id, title: book.title }),
      });
      if (!resp.ok) {
        const errData = await resp.json();
        throw new Error(errData.detail || "分析失败");
      }
      const data = await resp.json();
      setAnalysis(data);
    } catch (e) {
      setError("分析失败: " + e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app">
      <header className="app-header">
        <h1>CharWeave</h1>
        <p>书籍人物关系图谱自动生成工具</p>
      </header>

      <SearchPanel onSearch={handleSearch} />

      {error && <div className="error-msg">{error}</div>}
      {loading && <div className="loading">处理中...</div>}

      {results.length > 0 && !analysis && (
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
          <h2>《{analysis.title}》人物关系图</h2>
          <div className="characters">
            <h3>提取到的主要人物 ({analysis.characters.length})</h3>
            <div className="char-tags">
              {analysis.characters.map((c, i) => (
                <span key={i} className="char-tag">{c}</span>
              ))}
            </div>
          </div>
          <div className="mermaid-section">
            <h3>关系图谱</h3>
            <MermaidChart code={analysis.mermaid} />
          </div>
          <details className="mermaid-source">
            <summary>查看 Mermaid 源码</summary>
            <pre>{analysis.mermaid}</pre>
          </details>
          <button className="back-btn" onClick={() => setAnalysis(null)}>
            返回搜索结果
          </button>
        </div>
      )}
    </div>
  );
}

export default App;
