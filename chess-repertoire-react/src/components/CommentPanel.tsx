import React, { useState, useEffect } from 'react';

interface CommentPanelProps {
  currentComment: string;
  onCommentSave: (comment: string) => void;
}

const CommentPanel: React.FC<CommentPanelProps> = ({
  currentComment,
  onCommentSave
}) => {
  const [comment, setComment] = useState(currentComment);
  
  useEffect(() => {
    setComment(currentComment);
  }, [currentComment]);

  const handleSave = () => {
    onCommentSave(comment);
  };

  const handleKeyPress = (event: React.KeyboardEvent) => {
    if (event.key === 'Enter' && (event.ctrlKey || event.metaKey)) {
      handleSave();
    }
  };

  return (
    <div className="comment-panel">
      <h3>Position Comments</h3>
      <div className="comment-input-area">
        <textarea
          value={comment}
          onChange={(e) => setComment(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="Add a comment about this position..."
          rows={4}
          cols={50}
        />
        <div className="comment-actions">
          <button onClick={handleSave}>Save Comment</button>
          <small>Tip: Press Ctrl+Enter to save quickly</small>
        </div>
      </div>
    </div>
  );
};

export default CommentPanel;