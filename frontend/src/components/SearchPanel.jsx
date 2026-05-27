import { useState } from "react";

function SearchPanel({ onSearch }) {
  const [query, setQuery] = useState("");
  const [searchType, setSearchType] = useState("title");

  const handleSubmit = (e) => {
    e.preventDefault();
    if (query.trim()) {
      onSearch(query.trim(), searchType);
    }
  };

  return (
    <form className="search-panel" onSubmit={handleSubmit}>
      <div className="search-row">
        <select value={searchType} onChange={(e) => setSearchType(e.target.value)}>
          <option value="title">按书名</option>
          <option value="author">按作者</option>
        </select>
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="输入书名或作者名 (英文)..."
          className="search-input"
        />
        <button type="submit" className="search-btn">搜索</button>
      </div>
    </form>
  );
}

export default SearchPanel;
