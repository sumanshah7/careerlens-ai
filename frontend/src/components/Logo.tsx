import { Link } from 'react-router-dom';

export const Logo = ({ className = '' }: { className?: string }) => {
  return (
    <Link to="/" className={`flex items-center gap-2 group ${className}`}>
      <div className="relative">
        {/* Lens outer ring */}
        <svg
          width="32"
          height="32"
          viewBox="0 0 32 32"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
          className="transition-transform duration-200 group-hover:scale-105"
        >
          {/* Outer lens circle */}
          <circle
            cx="16"
            cy="16"
            r="14"
            stroke="currentColor"
            strokeWidth="1.5"
            className="text-[#0F172A] group-hover:text-[#2563EB] transition-colors"
          />
          {/* Inner lens circle */}
          <circle
            cx="16"
            cy="16"
            r="8"
            stroke="currentColor"
            strokeWidth="1.5"
            className="text-[#0F172A] group-hover:text-[#2563EB] transition-colors"
          />
          {/* Lens focus lines */}
          <line
            x1="16"
            y1="2"
            x2="16"
            y2="6"
            stroke="currentColor"
            strokeWidth="1.5"
            strokeLinecap="round"
            className="text-[#0F172A] group-hover:text-[#2563EB] transition-colors"
          />
          <line
            x1="16"
            y1="26"
            x2="16"
            y2="30"
            stroke="currentColor"
            strokeWidth="1.5"
            strokeLinecap="round"
            className="text-[#0F172A] group-hover:text-[#2563EB] transition-colors"
          />
          <line
            x1="2"
            y1="16"
            x2="6"
            y2="16"
            stroke="currentColor"
            strokeWidth="1.5"
            strokeLinecap="round"
            className="text-[#0F172A] group-hover:text-[#2563EB] transition-colors"
          />
          <line
            x1="26"
            y1="16"
            x2="30"
            y2="16"
            stroke="currentColor"
            strokeWidth="1.5"
            strokeLinecap="round"
            className="text-[#0F172A] group-hover:text-[#2563EB] transition-colors"
          />
          {/* Center dot (focus point) */}
          <circle
            cx="16"
            cy="16"
            r="1.5"
            fill="currentColor"
            className="text-[#2563EB]"
          />
        </svg>
      </div>
      <span className="text-lg font-semibold text-[#0F172A] group-hover:text-[#2563EB] transition-colors">
        CareerLens AI
      </span>
    </Link>
  );
};

