import { Globe, Trash2 } from 'lucide-react';

interface Props {
  messageCount: number;
  onClear: () => void;
}

export function Header({ messageCount, onClear }: Props) {
  return (
    <header className="flex items-center justify-between px-6 py-4 border-b border-ink-200 bg-white/80 backdrop-blur-sm sticky top-0 z-10">
      <div className="flex items-center gap-3">
        <div className="w-8 h-8 bg-ink-900 rounded-sm flex items-center justify-center">
          <Globe size={16} className="text-ink-100" />
        </div>
        <div>
          <h1 className="font-display text-lg font-semibold text-ink-900 leading-none">
            Vishwa
          </h1>
          <p className="text-xs text-ink-500 font-mono mt-0.5">Country Intelligence Agent</p>
        </div>
      </div>

      <div className="flex items-center gap-3">
        {messageCount > 0 && (
          <>
            <span className="text-xs text-ink-400 font-mono hidden sm:block">
              {Math.floor(messageCount / 2)} question{messageCount > 2 ? 's' : ''}
            </span>
            <button
              onClick={onClear}
              className="flex items-center gap-1.5 text-xs text-ink-500 hover:text-ink-800 border border-ink-200 hover:border-ink-400 px-2.5 py-1.5 rounded-sm transition-all duration-150 font-body"
            >
              <Trash2 size={12} />
              Clear
            </button>
          </>
        )}
      </div>
    </header>
  );
}
