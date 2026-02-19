import React from 'react';

interface LogoProps {
  size?: 'small' | 'medium' | 'large';
  className?: string;
}

const Logo: React.FC<LogoProps> = ({ size = 'medium', className = '' }) => {
  const sizes = {
    small: { text: 'text-xl', icon: 'w-8 h-8' },
    medium: { text: 'text-3xl', icon: 'w-12 h-12' },
    large: { text: 'text-4xl', icon: 'w-16 h-16' }
  };

  return (
    <div className={`flex items-center gap-3 ${className}`}>
      {/* Glassmorphism icon */}
      <div className={`${sizes[size].icon} rounded-2xl bg-white/10 backdrop-blur-md shadow-xl flex items-center justify-center border border-white/20`}>
        <svg
          className="w-2/3 h-2/3 text-white drop-shadow-lg"
          viewBox="0 0 24 24"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
        >
          {/* Face outline */}
          <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="2.5" fill="none" />
          {/* Eyes */}
          <circle cx="9" cy="10" r="1.5" fill="currentColor" />
          <circle cx="15" cy="10" r="1.5" fill="currentColor" />
          {/* Smile */}
          <path
            d="M8 14.5 Q12 17 16 14.5"
            stroke="currentColor"
            strokeWidth="2.5"
            fill="none"
            strokeLinecap="round"
          />
          {/* Search magnifier overlay */}
          <circle cx="17" cy="17" r="3" stroke="currentColor" strokeWidth="2.5" fill="rgba(255,255,255,0.2)" />
          <line x1="19" y1="19" x2="21" y2="21" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" />
        </svg>
      </div>
      <span className={`font-bold ${sizes[size].text} text-white drop-shadow-lg`}>
        TraceFace
      </span>
    </div>
  );
};

export default Logo;
