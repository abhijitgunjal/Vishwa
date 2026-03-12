import { useState, useCallback, useRef } from 'react';
import { queryCountry, ApiError } from '../lib/api';
import type { Message } from '../types';

function generateId(): string {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
}

function getErrorMessage(err: unknown): string {
  if (err instanceof ApiError) {
    switch (err.status) {
      case 429: return 'Too many requests — please wait a moment before asking again.';
      case 422: return 'Your question could not be understood. Please try rephrasing it.';
      case 500: return 'The agent encountered an internal error. Please try again.';
      default:  return `Something went wrong (${err.status}). Please try again.`;
    }
  }
  return 'Failed to reach the agent. Is the backend running?';
}

export function useChat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const abortRef = useRef<AbortController | null>(null);

  const sendMessage = useCallback(async (question: string) => {
    if (!question.trim() || isLoading) return;

    const userMsg: Message = {
      id: generateId(),
      role: 'user',
      content: question.trim(),
      timestamp: new Date(),
    };

    const assistantId = generateId();
    const loadingMsg: Message = {
      id: assistantId,
      role: 'assistant',
      content: '',
      status: 'loading',
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMsg, loadingMsg]);
    setIsLoading(true);
    abortRef.current = new AbortController();

    try {
      const data = await queryCountry(question, abortRef.current.signal);
      setMessages((prev) =>
        prev.map((m) =>
          m.id === assistantId
            ? { ...m, content: data.answer, status: 'done' }
            : m
        )
      );
    } catch (err) {
      if ((err as Error).name === 'AbortError') return;

      setMessages((prev) =>
        prev.map((m) =>
          m.id === assistantId
            ? { ...m, content: getErrorMessage(err), status: 'error', error: true }
            : m
        )
      );
    } finally {
      setIsLoading(false);
      abortRef.current = null;
    }
  }, [isLoading]);

  const cancelRequest = useCallback(() => {
    abortRef.current?.abort();
    setIsLoading(false);
  }, []);

  const clearMessages = useCallback(() => {
    setMessages([]);
  }, []);

  return { messages, isLoading, sendMessage, cancelRequest, clearMessages };
}
