import type { StreamableMessage } from "../types";
import "./MessageItem.css";

interface MessageItemProps {
  message: StreamableMessage;
}

function MessageItem({ message }: MessageItemProps) {
  const getLevelIcon = (level: string) => {
    switch (level) {
      case "success":
        return "✓";
      case "error":
      case "bug":
        return "✗";
      case "warning":
        return "⚠";
      case "info":
        return "ℹ";
      case "improvement":
        return "→";
      case "vulnerability":
        return "🔒";
      case "malicious":
        return "⚡";
      default:
        return "•";
    }
  };

  return (
    <div className={`message-item level-${message.level}`}>
      <span className="message-icon">{getLevelIcon(message.level)}</span>
      <span className="message-text">{message.message}</span>
    </div>
  );
}

export default MessageItem;
