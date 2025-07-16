# Test Project Structure

This repository contains sample React components and project structure that serve as test cases for the Palette CLI tool.

## 📁 Project Structure Purpose

### `app/` Directory
- **Purpose**: Simulates a Next.js 13+ app router structure
- **Contains**: Sample pages using the new app directory convention
- **Used by**: Project analyzer to detect framework (Next.js) and styling patterns

### `components/` Directory  
- **Purpose**: Contains sample React components for analysis
- **Contains**: Example components with various CSS classes and styling patterns
- **Used by**: Color extraction logic to identify design tokens and component patterns

### Current Test Components

#### `app/profile/page.tsx`
```tsx
const ProfilePage = () => {
  return (
    <div className="bg-background text-foreground">
      <h1>Profile Page</h1>
    </div>
  );
};
```

#### `components/Button.tsx`
```tsx
const Button = () => {
  return <button className="bg-primary text-white">Click me</button>;
};
```

## 🎯 How These Are Used

The Palette CLI analyzer:

1. **Framework Detection**: Sees `app/` directory → detects Next.js
2. **Component Analysis**: Scans `.tsx` files for className patterns
3. **Color Extraction**: Finds colors like "white", "primary", "background" 
4. **Design Token Discovery**: Builds a picture of the project's design system

## 🧪 Testing

These components are essential for testing the CLI functionality:

```bash
# Test the analyzer
python3 palette.py analyze

# Expected output:
# Framework: next.js
# Styling: css  
# Colors: white, primary, background, foreground
```

## 📝 Adding More Test Cases

To test additional scenarios, you can add:

- More components with different styling patterns
- CSS files with custom properties
- `tailwind.config.js` for Tailwind-specific testing
- Different component library patterns (shadcn/ui, etc.)

## ⚡ Quick Test

```bash
# Run all tests
python3 tests/test_cli.py

# Run pytest suite
python3 -m pytest tests/ -v

# Test CLI directly
python3 palette.py analyze
```

The test components help ensure the Palette CLI can correctly analyze real-world React projects and extract meaningful design information!
