interface Props {
  onSelect: (q: string) => void;
}

const SUGGESTIONS = [
  'What is the population of Germany?',
  'What currency does Japan use?',
  'What is the capital of Brazil?',
  'Tell me about France — capital, currency and population',
  'What languages are spoken in Switzerland?',
  'What is the area of Australia?',
];

export function SuggestedQuestions({ onSelect }: Props) {
  return (
    <div className="flex flex-wrap gap-2 justify-center max-w-2xl mx-auto px-4">
      {SUGGESTIONS.map((q) => (
        <button
          key={q}
          onClick={() => onSelect(q)}
          className="px-3 py-1.5 text-xs font-body text-ink-600 border border-ink-200 rounded-sm bg-white hover:bg-ink-50 hover:border-ink-400 hover:text-ink-900 transition-all duration-150 text-left"
        >
          {q}
        </button>
      ))}
    </div>
  );
}
