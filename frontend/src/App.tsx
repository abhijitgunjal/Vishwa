import { useRef, useEffect } from 'react';
import { Header } from './components/Header';
import { MessageBubble } from './components/MessageBubble';
import { ChatInput } from './components/ChatInput';
import { EmptyState } from './components/EmptyState';
import { useChat } from './hooks/useChat';

export default function App() {
  const { messages, isLoading, sendMessage, cancelRequest, clearMessages } = useChat();
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  return (
    <div className="flex flex-col h-screen bg-ink-50 font-body">
      <Header messageCount={messages.length} onClear={clearMessages} />

      <main className="flex-1 overflow-y-auto">
        {messages.length === 0 ? (
          <EmptyState onSelect={sendMessage} />
        ) : (
          <div className="max-w-3xl mx-auto px-4 py-6 flex flex-col gap-6">
            {messages.map((message) => (
              <MessageBubble key={message.id} message={message} />
            ))}
            <div ref={bottomRef} />
          </div>
        )}
      </main>

      <footer className="border-t border-ink-200 bg-white/90 backdrop-blur-sm px-4 py-4">
        <div className="max-w-3xl mx-auto">
          <ChatInput
            onSend={sendMessage}
            onCancel={cancelRequest}
            isLoading={isLoading}
          />
          <p className="text-center text-xs text-ink-400 font-mono mt-2">
            Press <kbd className="bg-ink-100 px-1 rounded text-ink-600">Enter</kbd> to send ·{' '}
            <kbd className="bg-ink-100 px-1 rounded text-ink-600">Shift+Enter</kbd> for newline
          </p>
        </div>
      </footer>
    </div>
  );
}
