import React from 'react';
import { GraduationCap, Lightbulb, Globe, Dumbbell } from 'lucide-react';
import { useSettings } from '@/context/SettingsContext';
import { LogoPreview } from '@/components/SettingsModal';

const suggestionIcons = [GraduationCap, Lightbulb, Globe, Dumbbell];

const WelcomeScreen = ({ suggestions, onSuggestionClick }) => {
  const { settings } = useSettings();

  return (
    <div className="flex-1 flex flex-col items-center justify-center px-4 pb-4">
      <div className="flex flex-col items-center max-w-2xl w-full">
        {/* Logo */}
        <div className="mb-6">
          <LogoPreview settings={settings} size={48} />
        </div>

        {/* Greeting */}
        <h1 className="text-[28px] font-semibold mb-8" style={{ color: 'var(--text-primary)' }}>
          How can I help you today?
        </h1>

        {/* Suggestions */}
        <div className="grid grid-cols-2 gap-2.5 w-full max-w-xl">
          {suggestions.map((suggestion, index) => {
            const Icon = suggestionIcons[index % suggestionIcons.length];
            return (
              <button
                key={index}
                onClick={() => onSuggestionClick(suggestion)}
                className="flex items-start gap-3 p-3.5 rounded-xl border border-white/10 hover:bg-white/5 transition-all duration-200 text-left group"
              >
                <div className="mt-0.5 text-neutral-500 group-hover:text-neutral-300 transition-colors">
                  <Icon size={18} />
                </div>
                <div className="flex flex-col min-w-0">
                  <span className="text-sm font-medium text-neutral-200">
                    {suggestion.title}
                  </span>
                  <span className="text-sm text-neutral-500 truncate">
                    {suggestion.subtitle}
                  </span>
                </div>
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
};

export default WelcomeScreen;
