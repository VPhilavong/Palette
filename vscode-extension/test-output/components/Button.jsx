// TestButton.tsx

import * as React from "react";
import "./TestButton.css";

export interface TestButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  /**
   * Handler for click events.
   */
  onClick: (event: React.MouseEvent<HTMLButtonElement>) => void;
  /**
   * Button contents (text, icon, etc.).
   */
  children: React.ReactNode;
  /**
   * Visually and functionally disables the button.
   * Default: false
   */
  disabled?: boolean;
  /**
   * Accessible label for screen readers.
   * If not set, children (if plain text) will be used as fallback.
   */
  ariaLabel?: string;
  /**
   * Visual color scheme for the button.
   * Accepts: 'blue', 'gray', 'green', 'red', 'yellow'
   * Default: 'blue'
   */
  color?: "blue" | "gray" | "green" | "red" | "yellow";
}

/**
 * A reusable, accessible, and WCAG 2.1 AA-compliant button component.
 */
export const TestButton = React.memo(
  React.forwardRef<HTMLButtonElement, TestButtonProps>(
    (
      {
        onClick,
        children,
        disabled = false,
        ariaLabel,
        color = "blue",
        className = "",
        ...rest
      },
      ref
    ) => {
      // Compute final aria-label
      const label =
        ariaLabel ||
        (typeof children === "string" ? children : undefined) ||
        undefined;

      // Ensure "aria-disabled" is set even when disabled is true
      // Prevent onClick firing when disabled for safety
      const handleClick: React.MouseEventHandler<HTMLButtonElement> = e => {
        if (disabled) {
          e.preventDefault();
          e.stopPropagation();
          return;
        }
        onClick?.(e);
      };

      // Compose class names
      const colorClass = `test-button--${color}`;
      const isDisabledClass = disabled ? "is-disabled" : "";
      const combinedClassName = `test-button ${colorClass} ${isDisabledClass} ${className}`.trim();

      return (
        <button
          ref={ref}
          type="button"
          className={combinedClassName}
          onClick={handleClick}
          disabled={disabled}
          aria-label={label}
          aria-disabled={disabled}
          tabIndex={disabled ? -1 : 0}
          {...rest}
        >
          {children}
        </button>
      );
    }
  )
);

TestButton.displayName = "TestButton";

export default TestButton;

/*
Usage Example:

import * as React from "react";
import TestButton from "./TestButton";

function Example() {
  const handleClick = () => {
    alert("Test button clicked!");
  };

  return (
    <div>
      <TestButton onClick={handleClick} color="green" ariaLabel="Test action button">
        Test Button
      </TestButton>
    </div>
  );
}

*/

/* --- TestButton.css example ---
.test-button {
  font-size: 1rem;
  font-family: inherit;
  padding: 0.5em 1.5em;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  transition:
    background 0.15s,
    box-shadow 0.13s;
  outline: 2px solid transparent;
  outline-offset: 2px;
  min-width: 44px;
  min-height: 44px; /* meets WCAG AA size */
  line-height: 1.3;
}

.test-button:focus-visible {
  outline: 2px solid #2563eb;
  outline-offset: 2px;
}

.test-button.is-disabled,
.test-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* Color variants using available colors */
.test-button--blue { background: #2563eb; color: #fff; }
.test-button--gray { background: #6b7280; color: #fff; }
.test-button--green { background: #22c55e; color: #fff; }
.test-button--red { background: #ef4444; color: #fff; }
.test-button--yellow { background: #eab308; color: #222; }
*/

/* Accessible hover & active states */
.test-button:not(.is-disabled):not(:disabled):hover,
.test-button:not(.is-disabled):not(:disabled):active {
  filter: brightness(0.95);
  box-shadow: 0 0 0 3px rgba(37,99,235,.12);
}