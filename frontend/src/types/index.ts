export type MessageRole = 'user' | 'assistant';

export type MessageStatus = 'loading' | 'done' | 'error';

export interface Message {
  id: string;
  role: MessageRole;
  content: string;
  status?: MessageStatus;
  timestamp: Date;
  error?: boolean;
}

export interface ChatSession {
  id: string;
  messages: Message[];
  createdAt: Date;
}
