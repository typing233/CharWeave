import { useEffect, useRef } from "react";
import mermaid from "mermaid";

mermaid.initialize({
  startOnLoad: false,
  theme: "default",
  securityLevel: "loose",
});

function MermaidChart({ code }) {
  const containerRef = useRef(null);

  useEffect(() => {
    if (!code || !containerRef.current) return;

    const id = "mermaid-" + Date.now();
    containerRef.current.innerHTML = "";

    mermaid.render(id, code).then(({ svg }) => {
      if (containerRef.current) {
        containerRef.current.innerHTML = svg;
      }
    }).catch((err) => {
      if (containerRef.current) {
        containerRef.current.innerHTML = `<pre class="mermaid-error">渲染失败: ${err.message}</pre>`;
      }
    });
  }, [code]);

  return <div ref={containerRef} className="mermaid-container" />;
}

export default MermaidChart;
