function GraphExport({ graphRef, mermaidCode }) {
  const downloadBlob = (blob, filename) => {
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const exportSVG = () => {
    const svgEl = graphRef.current?.getSvgElement();
    if (!svgEl) return;
    const clone = svgEl.cloneNode(true);
    clone.setAttribute("xmlns", "http://www.w3.org/2000/svg");
    // Inline basic styles for standalone SVG
    const style = document.createElement("style");
    style.textContent = `
      text { font-family: sans-serif; }
      line { stroke-linecap: round; }
    `;
    clone.insertBefore(style, clone.firstChild);
    const serializer = new XMLSerializer();
    const svgString = serializer.serializeToString(clone);
    const blob = new Blob([svgString], { type: "image/svg+xml;charset=utf-8" });
    downloadBlob(blob, "charweave-graph.svg");
  };

  const exportPNG = () => {
    const svgEl = graphRef.current?.getSvgElement();
    if (!svgEl) return;
    const clone = svgEl.cloneNode(true);
    clone.setAttribute("xmlns", "http://www.w3.org/2000/svg");
    const serializer = new XMLSerializer();
    const svgString = serializer.serializeToString(clone);
    const svgBlob = new Blob([svgString], { type: "image/svg+xml;charset=utf-8" });
    const url = URL.createObjectURL(svgBlob);
    const img = new Image();
    img.onload = () => {
      const canvas = document.createElement("canvas");
      const scale = 2; // High DPI
      canvas.width = svgEl.clientWidth * scale;
      canvas.height = svgEl.clientHeight * scale;
      const ctx = canvas.getContext("2d");
      ctx.scale(scale, scale);
      ctx.fillStyle = "#ffffff";
      ctx.fillRect(0, 0, canvas.width, canvas.height);
      ctx.drawImage(img, 0, 0);
      URL.revokeObjectURL(url);
      canvas.toBlob((blob) => {
        if (blob) downloadBlob(blob, "charweave-graph.png");
      }, "image/png");
    };
    img.src = url;
  };

  const exportMermaid = () => {
    if (!mermaidCode) return;
    const blob = new Blob([mermaidCode], { type: "text/plain;charset=utf-8" });
    downloadBlob(blob, "charweave-graph.mmd");
  };

  return (
    <div className="graph-export">
      <span className="export-label">导出图谱:</span>
      <button className="export-btn export-svg" onClick={exportSVG} title="下载 SVG 矢量图">
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M8 10L4 6h3V2h2v4h3L8 10z" fill="currentColor"/>
          <path d="M13 12H3v2h10v-2z" fill="currentColor"/>
        </svg>
        SVG
      </button>
      <button className="export-btn export-png" onClick={exportPNG} title="下载 PNG 图片">
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M8 10L4 6h3V2h2v4h3L8 10z" fill="currentColor"/>
          <path d="M13 12H3v2h10v-2z" fill="currentColor"/>
        </svg>
        PNG
      </button>
      <button className="export-btn export-mermaid" onClick={exportMermaid} title="下载 Mermaid 代码">
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M8 10L4 6h3V2h2v4h3L8 10z" fill="currentColor"/>
          <path d="M13 12H3v2h10v-2z" fill="currentColor"/>
        </svg>
        Mermaid
      </button>
    </div>
  );
}

export default GraphExport;
