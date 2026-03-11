import clsx from 'clsx';
import type { Message } from '../types';

interface Props {
  message: Message;
}

function formatTime(date: Date): string {
  return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
}

function LoadingDots() {
  return (
    <div className="flex items-center gap-1 px-1 py-0.5">
      {[0, 1, 2].map((i) => (
        <span
          key={i}
          className="w-1.5 h-1.5 rounded-full bg-ink-400 animate-pulse"
          style={{ animationDelay: `${i * 0.2}s` }}
        />
      ))}
    </div>
  );
}

export function MessageBubble({ message }: Props) {
  const isUser = message.role === 'user';
  const isLoading = message.status === 'loading';
  const isError = message.error;

  return (
    <div
      className={clsx(
        'flex w-full animate-slide-up',
        isUser ? 'justify-end' : 'justify-start'
      )}
    >
      {!isUser && (
        <div className="flex-shrink-0 w-8 h-8 rounded-sm bg-ink-900 flex items-center justify-center mr-3 mt-0.5 shadow-sm">
          <span className="text-ink-100 text-xs font-mono font-medium">V</span>
        </div>
      )}

      <div className={clsx('max-w-[75%] min-w-[60px] flex flex-col gap-1', isUser ? 'items-end' : 'items-start')}>
        <div
          className={clsx(
            'px-4 py-3 rounded-sm shadow-sm text-sm leading-relaxed',
            isUser
              ? 'bg-ink-900 text-ink-50 rounded-tr-none'
              : isError
              ? 'bg-red-50 border border-red-200 text-red-800 rounded-tl-none'
              : 'bg-white border border-ink-200 text-ink-800 rounded-tl-none'
          )}
        >
          {isLoading ? (
            <LoadingDots />
          ) : (
            <span className="font-body whitespace-pre-wrap">{message.content}</span>
          )}
        </div>

        <span className="text-xs text-ink-400 font-mono px-1">
          {formatTime(message.timestamp)}
        </span>
      </div>

      {isUser && (
        <div className="flex-shrink-0 w-8 h-8 rounded-sm bg-atlas-blue flex items-center justify-center ml-3 mt-0.5 shadow-sm">
          <span className="text-white text-xs font-mono font-medium">U</span>
        </div>
      )}
    </div>
  );
}
