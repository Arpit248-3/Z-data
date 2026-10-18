import React from 'react';
import { Sun, Moon } from 'lucide-react';
import { useTheme } from '../context/ThemeContext';

export const ThemeSwitcher: React.FC = () => {
  const { theme, toggleTheme } = useTheme();
  const isLight = theme === 'light';

  return (
    <button
      type="button"
      onClick={toggleTheme}
      className="theme-switcher-btn"
      aria-label={`Switch to ${isLight ? 'dark' : 'light'} theme`}
      title={`Switch to ${isLight ? 'Dark' : 'Light'} Theme`}
    >
      <div className={`theme-toggle-track ${isLight ? 'is-light' : 'is-dark'}`}>
        <div className="theme-toggle-thumb">
          {isLight ? (
            <Sun size={12} className="theme-icon sun-icon" />
          ) : (
            <Moon size={12} className="theme-icon moon-icon" />
          )}
        </div>
      </div>
      <span className="theme-mode-label">{isLight ? 'LIGHT' : 'DARK'}</span>
    </button>
  );
};
