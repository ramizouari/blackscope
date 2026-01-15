import { useState, type FormEvent } from "react";
import "./URLForm.css";

interface URLFormProps {
  onSubmit: (url: string) => void;
  isLoading: boolean;
}

function URLForm({ onSubmit, isLoading }: URLFormProps) {
  const [url, setUrl] = useState("");

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (url.trim()) {
      onSubmit(url.trim());
    }
  };

  return (
    <form className="url-form" onSubmit={handleSubmit}>
      <div className="form-group">
        <input
          type="text"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder="Enter URL to analyze (e.g., https://example.com)"
          disabled={isLoading}
          className="url-input"
        />
        <button type="submit" disabled={isLoading || !url.trim()} className="submit-btn">
          {isLoading ? "Analyzing..." : "Analyze"}
        </button>
      </div>
    </form>
  );
}

export default URLForm;
