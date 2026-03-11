import { Globe } from 'lucide-react';
import { SuggestedQuestions } from './SuggestedQuestions';

interface Props {
  onSelect: (q: string) => void;
}

export function EmptyState({ onSelect }: Props) {
  return (
    <div className="flex flex-col items-center justify-center h-full py-16 px-4 animate-fade-in">
      <div className="relative mb-8">
        <div className="w-20 h-20 rounded-full border-2 border-ink-200 flex items-center justify-center bg-white shadow-sm">
          <Globe size={36} className="text-ink-400" strokeWidth={1} />
        </div>
        <div className="absolute -top-1 -right-1 w-5 h-5 bg-atlas-blue rounded-full flex items-center justify-center">
          <span className="text-white text-xs">?</span>
        </div>
      </div>

      <h2 className="font-display text-2xl font-semibold text-ink-900 mb-2 text-center">
        Ask anything about the world
      </h2>
      <p className="text-sm text-ink-500 font-body text-center max-w-md mb-10 leading-relaxed">
        Vishwa is a LangGraph-powered agent that identifies your intent,
        queries live country data, and returns a grounded answer.
      </p>

      <div className="w-full">
        <p className="text-xs text-ink-400 font-mono text-center mb-3 uppercase tracking-widest">
          Try asking
        </p>
        <SuggestedQuestions onSelect={onSelect} />
      </div>

      <div className="mt-12 flex items-center gap-2 text-xs font-mono text-ink-400">
        <span className="text-atlas-blue">◎ Intent</span>
        <span className="text-ink-300">──</span>
        <span className="text-atlas-teal">⬡ Tool Call</span>
        <span className="text-ink-300">──</span>
        <span className="text-atlas-amber">◈ Synthesis</span>
      </div>
    </div>
  );
}
