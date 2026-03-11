import { useState, useRef, type KeyboardEvent } from 'react';
import { Send, Square } from 'lucide-react';
import clsx from 'clsx';

interface Props {
  onSend: (message: string) => void;
  onCancel: () => void;
  isLoading: boolean;
}

export function ChatInput({ onSend, onCancel, isLoading }: Props) {
  const [value, setValue] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSend = () => {
    const trimmed = value.trim();
    if (!trimmed || isLoading) return;
    onSend(trimmed);
    setValue('');
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleInput = () => {
    const ta = textareaRef.current;
    if (!ta) return;
    ta.style.height = 'auto';
    ta.style.height = `${Math.min(ta.scrollHeight, 160)}px`;
  };

  return (
    <div className="relative flex items-end gap-3 bg-white border border-ink-200 rounded-sm shadow-sm px-4 py-3 focus-within:border-ink-500 transition-colors duration-150">
      <textarea
        ref={textareaRef}
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onInput={handleInput}
        onKeyDown={handleKeyDown}
        placeholder="Ask about any country… e.g. What is the capital of Egypt?"
        rows={1}
        disabled={isLoading}
        className="flex-1 resize-none bg-transparent text-sm text-ink-800 placeholder-ink-400 font-body outline-none leading-relaxed min-h-[24px] max-h-[160px] disabled:opacity-50"
      />

      {isLoading ? (
        <button
          onClick={onCancel}
          className="flex-shrink-0 w-8 h-8 flex items-center justify-center rounded-sm bg-red-100 text-red-600 hover:bg-red-200 transition-colors"
          title="Cancel request"
        >
          <Square size={14} />
        </button>
      ) : (
        <button
          onClick={handleSend}
          disabled={!value.trim()}
          className={clsx(
            'flex-shrink-0 w-8 h-8 flex items-center justify-center rounded-sm transition-all duration-150',
            value.trim()
              ? 'bg-ink-900 text-white hover:bg-ink-700'
              : 'bg-ink-100 text-ink-400 cursor-not-allowed'
          )}
          title="Send (Enter)"
        >
          <Send size={14} />
        </button>
      )}
    </div>
  );
}
