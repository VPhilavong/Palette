#!/usr/bin/env python3
"""
Test Project Generator for Palette
Creates different types of test projects to validate Palette functionality:
- Vite + React + TypeScript + shadcn/ui (primary target)
- Next.js + shadcn/ui setup
- Basic React without TypeScript
- Project without Tailwind (for fallback testing)
"""

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, List

class TestProjectGenerator:
    def __init__(self, base_dir: str = None):
        self.base_dir = Path(base_dir) if base_dir else Path(__file__).parent / "test_projects"
        self.base_dir.mkdir(exist_ok=True)
        
    def create_all_test_projects(self):
        """Create all test project types"""
        print("🏗️  Creating test projects for Palette validation...")
        
        projects = [
            {
                "name": "vite-react-shadcn",
                "description": "Vite + React + TypeScript + shadcn/ui (Primary Target)",
                "creator": self.create_vite_react_shadcn_project
            },
            {
                "name": "next-shadcn",
                "description": "Next.js + shadcn/ui setup",
                "creator": self.create_nextjs_shadcn_project
            },
            {
                "name": "basic-react",
                "description": "Basic React without TypeScript",
                "creator": self.create_basic_react_project
            },
            {
                "name": "no-tailwind",
                "description": "React project without Tailwind (fallback testing)",
                "creator": self.create_no_tailwind_project
            }
        ]
        
        created_projects = []
        failed_projects = []
        
        for project in projects:
            try:
                print(f"\n📦 Creating {project['name']}: {project['description']}")
                project_path = project["creator"]()
                created_projects.append({
                    "name": project["name"],
                    "path": str(project_path),
                    "description": project["description"]
                })
                print(f"✅ Created: {project_path}")
            except Exception as e:
                print(f"❌ Failed to create {project['name']}: {e}")
                failed_projects.append({
                    "name": project["name"],
                    "error": str(e)
                })
        
        # Generate test project summary
        self.generate_project_summary(created_projects, failed_projects)
        
        return created_projects, failed_projects
    
    def create_vite_react_shadcn_project(self) -> Path:
        """Create Vite + React + TypeScript + shadcn/ui project"""
        project_dir = self.base_dir / "vite-react-shadcn"
        
        # Remove existing project
        if project_dir.exists():
            import shutil
            shutil.rmtree(project_dir)
        
        project_dir.mkdir(parents=True)
        
        # Create package.json
        package_json = {
            "name": "vite-react-shadcn-test",
            "private": True,
            "version": "0.0.0",
            "type": "module",
            "scripts": {
                "dev": "vite",
                "build": "tsc && vite build",
                "lint": "eslint . --ext ts,tsx --report-unused-disable-directives --max-warnings 0",
                "preview": "vite preview"
            },
            "dependencies": {
                "react": "^18.2.0",
                "react-dom": "^18.2.0",
                "@radix-ui/react-slot": "^1.0.2",
                "class-variance-authority": "^0.7.0",
                "clsx": "^2.0.0",
                "tailwind-merge": "^1.14.0",
                "lucide-react": "^0.263.1"
            },
            "devDependencies": {
                "@types/react": "^18.2.15",
                "@types/react-dom": "^18.2.7",
                "@typescript-eslint/eslint-plugin": "^6.0.0",
                "@typescript-eslint/parser": "^6.0.0",
                "@vitejs/plugin-react": "^4.0.3",
                "autoprefixer": "^10.4.14",
                "eslint": "^8.45.0",
                "eslint-plugin-react-hooks": "^4.6.0",
                "eslint-plugin-react-refresh": "^0.4.3",
                "postcss": "^8.4.27",
                "tailwindcss": "^3.3.3",
                "typescript": "^5.0.2",
                "vite": "^4.4.5"
            }
        }
        
        with open(project_dir / "package.json", "w") as f:
            json.dump(package_json, f, indent=2)
        
        # Create tsconfig.json
        tsconfig = {
            "compilerOptions": {
                "target": "ES2020",
                "useDefineForClassFields": True,
                "lib": ["ES2020", "DOM", "DOM.Iterable"],
                "module": "ESNext",
                "skipLibCheck": True,
                "moduleResolution": "bundler",
                "allowImportingTsExtensions": True,
                "resolveJsonModule": True,
                "isolatedModules": True,
                "noEmit": True,
                "jsx": "react-jsx",
                "strict": True,
                "noUnusedLocals": True,
                "noUnusedParameters": True,
                "noFallthroughCasesInSwitch": True,
                "baseUrl": ".",
                "paths": {
                    "@/*": ["./src/*"]
                }
            },
            "include": ["src"],
            "references": [{"path": "./tsconfig.node.json"}]
        }
        
        with open(project_dir / "tsconfig.json", "w") as f:
            json.dump(tsconfig, f, indent=2)
        
        # Create vite.config.ts
        vite_config = '''import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
})
'''
        
        with open(project_dir / "vite.config.ts", "w") as f:
            f.write(vite_config)
        
        # Create tailwind.config.js
        tailwind_config = '''/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: ["class"],
  content: [
    './pages/**/*.{ts,tsx}',
    './components/**/*.{ts,tsx}',
    './app/**/*.{ts,tsx}',
    './src/**/*.{ts,tsx}',
  ],
  theme: {
    container: {
      center: true,
      padding: "2rem",
      screens: {
        "2xl": "1400px",
      },
    },
    extend: {
      colors: {
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
        },
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },
        popover: {
          DEFAULT: "hsl(var(--popover))",
          foreground: "hsl(var(--popover-foreground))",
        },
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
      },
      keyframes: {
        "accordion-down": {
          from: { height: 0 },
          to: { height: "var(--radix-accordion-content-height)" },
        },
        "accordion-up": {
          from: { height: "var(--radix-accordion-content-height)" },
          to: { height: 0 },
        },
      },
      animation: {
        "accordion-down": "accordion-down 0.2s ease-out",
        "accordion-up": "accordion-up 0.2s ease-out",
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
}
'''
        
        with open(project_dir / "tailwind.config.js", "w") as f:
            f.write(tailwind_config)
        
        # Create components.json (shadcn/ui config)
        components_json = {
            "$schema": "https://ui.shadcn.com/schema.json",
            "style": "default",
            "rsc": False,
            "tsx": True,
            "tailwind": {
                "config": "tailwind.config.js",
                "css": "src/index.css",
                "baseColor": "slate",
                "cssVariables": True
            },
            "aliases": {
                "components": "@/components",
                "utils": "@/lib/utils"
            }
        }
        
        with open(project_dir / "components.json", "w") as f:
            json.dump(components_json, f, indent=2)
        
        # Create src directory structure
        src_dir = project_dir / "src"
        src_dir.mkdir()
        
        # Create lib/utils.ts
        lib_dir = src_dir / "lib"
        lib_dir.mkdir()
        
        utils_ts = '''import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}
'''
        
        with open(lib_dir / "utils.ts", "w") as f:
            f.write(utils_ts)
        
        # Create components/ui directory
        components_dir = src_dir / "components" / "ui"
        components_dir.mkdir(parents=True)
        
        # Create button component
        button_tsx = '''import * as React from "react"
import { Slot } from "@radix-ui/react-slot"
import { cva, type VariantProps } from "class-variance-authority"

import { cn } from "@/lib/utils"

const buttonVariants = cva(
  "inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50",
  {
    variants: {
      variant: {
        default: "bg-primary text-primary-foreground hover:bg-primary/90",
        destructive:
          "bg-destructive text-destructive-foreground hover:bg-destructive/90",
        outline:
          "border border-input bg-background hover:bg-accent hover:text-accent-foreground",
        secondary:
          "bg-secondary text-secondary-foreground hover:bg-secondary/80",
        ghost: "hover:bg-accent hover:text-accent-foreground",
        link: "text-primary underline-offset-4 hover:underline",
      },
      size: {
        default: "h-10 px-4 py-2",
        sm: "h-9 rounded-md px-3",
        lg: "h-11 rounded-md px-8",
        icon: "h-10 w-10",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
)

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : "button"
    return (
      <Comp
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        {...props}
      />
    )
  }
)
Button.displayName = "Button"

export { Button, buttonVariants }
'''
        
        with open(components_dir / "button.tsx", "w") as f:
            f.write(button_tsx)
        
        # Create index.css
        index_css = '''@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  :root {
    --background: 0 0% 100%;
    --foreground: 222.2 84% 4.9%;
    --card: 0 0% 100%;
    --card-foreground: 222.2 84% 4.9%;
    --popover: 0 0% 100%;
    --popover-foreground: 222.2 84% 4.9%;
    --primary: 222.2 47.4% 11.2%;
    --primary-foreground: 210 40% 98%;
    --secondary: 210 40% 96%;
    --secondary-foreground: 222.2 47.4% 11.2%;
    --muted: 210 40% 96%;
    --muted-foreground: 215.4 16.3% 46.9%;
    --accent: 210 40% 96%;
    --accent-foreground: 222.2 47.4% 11.2%;
    --destructive: 0 84.2% 60.2%;
    --destructive-foreground: 210 40% 98%;
    --border: 214.3 31.8% 91.4%;
    --input: 214.3 31.8% 91.4%;
    --ring: 222.2 84% 4.9%;
    --radius: 0.5rem;
  }

  .dark {
    --background: 222.2 84% 4.9%;
    --foreground: 210 40% 98%;
    --card: 222.2 84% 4.9%;
    --card-foreground: 210 40% 98%;
    --popover: 222.2 84% 4.9%;
    --popover-foreground: 210 40% 98%;
    --primary: 210 40% 98%;
    --primary-foreground: 222.2 47.4% 11.2%;
    --secondary: 217.2 32.6% 17.5%;
    --secondary-foreground: 210 40% 98%;
    --muted: 217.2 32.6% 17.5%;
    --muted-foreground: 215 20.2% 65.1%;
    --accent: 217.2 32.6% 17.5%;
    --accent-foreground: 210 40% 98%;
    --destructive: 0 62.8% 30.6%;
    --destructive-foreground: 210 40% 98%;
    --border: 217.2 32.6% 17.5%;
    --input: 217.2 32.6% 17.5%;
    --ring: 212.7 26.8% 83.9%;
  }
}

@layer base {
  * {
    @apply border-border;
  }
  body {
    @apply bg-background text-foreground;
  }
}
'''
        
        with open(src_dir / "index.css", "w") as f:
            f.write(index_css)
        
        # Create App.tsx
        app_tsx = '''import { Button } from '@/components/ui/button'
import './index.css'

function App() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="container mx-auto px-4 py-16">
        <div className="text-center">
          <h1 className="text-4xl font-bold text-gray-900 mb-8">
            Palette Test Project
          </h1>
          <p className="text-lg text-gray-600 mb-8">
            Vite + React + TypeScript + shadcn/ui
          </p>
          <div className="space-x-4">
            <Button>Primary Button</Button>
            <Button variant="outline">Outline Button</Button>
            <Button variant="secondary">Secondary Button</Button>
          </div>
        </div>
      </div>
    </div>
  )
}

export default App
'''
        
        with open(src_dir / "App.tsx", "w") as f:
            f.write(app_tsx)
        
        # Create main.tsx
        main_tsx = '''import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.tsx'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
'''
        
        with open(src_dir / "main.tsx", "w") as f:
            f.write(main_tsx)
        
        # Create index.html
        index_html = '''<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/vite.svg" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Palette Test Project</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
'''
        
        with open(project_dir / "index.html", "w") as f:
            f.write(index_html)
        
        # Create README
        readme = '''# Vite + React + TypeScript + shadcn/ui Test Project

This is a test project for Palette AI with the primary target stack:
- ⚡ Vite for fast development
- ⚛️  React 18
- 📘 TypeScript for type safety  
- 🎨 Tailwind CSS for styling
- 🧩 shadcn/ui for components

## Usage

1. Install dependencies: `npm install`
2. Start development: `npm run dev`
3. Test Palette generation in this project

## Palette Test Scenarios

Try these prompts with Palette:

### Simple Components (AI SDK Route)
- "Create a simple card component"
- "Make a basic form with email and password"

### Complex Pages (Python Backend Route)  
- "Create a complete dashboard with sidebar and charts"
- "Build a landing page with hero, features, and pricing"
- "Generate an e-commerce product page with gallery and reviews"
'''
        
        with open(project_dir / "README.md", "w") as f:
            f.write(readme)
        
        return project_dir
    
    def create_nextjs_shadcn_project(self) -> Path:
        """Create Next.js + shadcn/ui project"""
        project_dir = self.base_dir / "next-shadcn"
        
        if project_dir.exists():
            import shutil
            shutil.rmtree(project_dir)
        
        project_dir.mkdir(parents=True)
        
        # Create package.json
        package_json = {
            "name": "next-shadcn-test",
            "version": "0.1.0",
            "private": True,
            "scripts": {
                "dev": "next dev",
                "build": "next build", 
                "start": "next start",
                "lint": "next lint"
            },
            "dependencies": {
                "react": "^18",
                "react-dom": "^18",
                "next": "14.0.0",
                "@radix-ui/react-slot": "^1.0.2",
                "class-variance-authority": "^0.7.0",
                "clsx": "^2.0.0",
                "tailwind-merge": "^1.14.0"
            },
            "devDependencies": {
                "typescript": "^5",
                "@types/node": "^20",
                "@types/react": "^18",
                "@types/react-dom": "^18",
                "autoprefixer": "^10.0.1",
                "postcss": "^8",
                "tailwindcss": "^3.3.0",
                "eslint": "^8",
                "eslint-config-next": "14.0.0"
            }
        }
        
        with open(project_dir / "package.json", "w") as f:
            json.dump(package_json, f, indent=2)
        
        # Create next.config.js
        next_config = '''/** @type {import('next').NextConfig} */
const nextConfig = {}

module.exports = nextConfig
'''
        
        with open(project_dir / "next.config.js", "w") as f:
            f.write(next_config)
        
        # Create tailwind config (similar to Vite version)
        with open(project_dir / "tailwind.config.js", "w") as f:
            f.write('''/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: ["class"],
  content: [
    './pages/**/*.{ts,tsx}',
    './components/**/*.{ts,tsx}',
    './app/**/*.{ts,tsx}',
    './src/**/*.{ts,tsx}',
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}
''')
        
        # Create tsconfig.json
        tsconfig = {
            "compilerOptions": {
                "target": "es5",
                "lib": ["dom", "dom.iterable", "es6"],
                "allowJs": True,
                "skipLibCheck": True,
                "strict": True,
                "noEmit": True,
                "esModuleInterop": True,
                "module": "esnext",
                "moduleResolution": "bundler",
                "resolveJsonModule": True,
                "isolatedModules": True,
                "jsx": "preserve",
                "incremental": True,
                "plugins": [
                    {
                        "name": "next"
                    }
                ],
                "baseUrl": ".",
                "paths": {
                    "@/*": ["./src/*"]
                }
            },
            "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx", ".next/types/**/*.ts"],
            "exclude": ["node_modules"]
        }
        
        with open(project_dir / "tsconfig.json", "w") as f:
            json.dump(tsconfig, f, indent=2)
        
        # Create src/app structure
        app_dir = project_dir / "src" / "app"
        app_dir.mkdir(parents=True)
        
        # Create layout.tsx
        layout_tsx = '''import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'Next.js + shadcn/ui Test',
  description: 'Test project for Palette AI',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className={inter.className}>{children}</body>
    </html>
  )
}
'''
        
        with open(app_dir / "layout.tsx", "w") as f:
            f.write(layout_tsx)
        
        # Create page.tsx
        page_tsx = '''export default function Home() {
  return (
    <main className="min-h-screen bg-gradient-to-br from-purple-50 to-pink-100">
      <div className="container mx-auto px-4 py-16">
        <div className="text-center">
          <h1 className="text-4xl font-bold text-gray-900 mb-8">
            Next.js + shadcn/ui Test
          </h1>
          <p className="text-lg text-gray-600 mb-8">
            Perfect for testing Palette with Next.js framework
          </p>
        </div>
      </div>
    </main>
  )
}
'''
        
        with open(app_dir / "page.tsx", "w") as f:
            f.write(page_tsx)
        
        # Create globals.css
        globals_css = '''@tailwind base;
@tailwind components;
@tailwind utilities;
'''
        
        with open(app_dir / "globals.css", "w") as f:
            f.write(globals_css)
        
        return project_dir
    
    def create_basic_react_project(self) -> Path:
        """Create basic React project without TypeScript"""
        project_dir = self.base_dir / "basic-react"
        
        if project_dir.exists():
            import shutil
            shutil.rmtree(project_dir)
        
        project_dir.mkdir(parents=True)
        
        # Create package.json
        package_json = {
            "name": "basic-react-test",
            "version": "0.1.0",
            "private": True,
            "dependencies": {
                "react": "^18.2.0",
                "react-dom": "^18.2.0",
                "react-scripts": "5.0.1"
            },
            "scripts": {
                "start": "react-scripts start",
                "build": "react-scripts build",
                "test": "react-scripts test",
                "eject": "react-scripts eject"
            },
            "eslintConfig": {
                "extends": [
                    "react-app",
                    "react-app/jest"
                ]
            },
            "browserslist": {
                "production": [
                    ">0.2%",
                    "not dead",
                    "not op_mini all"
                ],
                "development": [
                    "last 1 chrome version",
                    "last 1 firefox version",
                    "last 1 safari version"
                ]
            }
        }
        
        with open(project_dir / "package.json", "w") as f:
            json.dump(package_json, f, indent=2)
        
        # Create src directory
        src_dir = project_dir / "src"
        src_dir.mkdir()
        
        # Create App.js
        app_js = '''import React from 'react';
import './App.css';

function App() {
  return (
    <div className="App">
      <header className="App-header">
        <h1>Basic React Test Project</h1>
        <p>No TypeScript, no Tailwind - testing fallbacks</p>
      </header>
    </div>
  );
}

export default App;
'''
        
        with open(src_dir / "App.js", "w") as f:
            f.write(app_js)
        
        # Create App.css
        app_css = '''.App {
  text-align: center;
}

.App-header {
  background-color: #282c34;
  padding: 20px;
  color: white;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  font-size: calc(10px + 2vmin);
}
'''
        
        with open(src_dir / "App.css", "w") as f:
            f.write(app_css)
        
        # Create index.js
        index_js = '''import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App';

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
'''
        
        with open(src_dir / "index.js", "w") as f:
            f.write(index_js)
        
        # Create index.css
        index_css = '''body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen',
    'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue',
    sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

code {
  font-family: source-code-pro, Menlo, Monaco, Consolas, 'Courier New',
    monospace;
}
'''
        
        with open(src_dir / "index.css", "w") as f:
            f.write(index_css)
        
        # Create public directory
        public_dir = project_dir / "public"
        public_dir.mkdir()
        
        # Create index.html
        index_html = '''<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <meta name="theme-color" content="#000000" />
    <meta name="description" content="Basic React test app for Palette" />
    <title>Basic React Test</title>
  </head>
  <body>
    <noscript>You need to enable JavaScript to run this app.</noscript>
    <div id="root"></div>
  </body>
</html>
'''
        
        with open(public_dir / "index.html", "w") as f:
            f.write(index_html)
        
        return project_dir
    
    def create_no_tailwind_project(self) -> Path:
        """Create React project without Tailwind CSS"""
        project_dir = self.base_dir / "no-tailwind"
        
        if project_dir.exists():
            import shutil
            shutil.rmtree(project_dir)
        
        project_dir.mkdir(parents=True)
        
        # Create package.json  
        package_json = {
            "name": "no-tailwind-test",
            "version": "0.1.0",
            "private": True,
            "type": "module",
            "scripts": {
                "dev": "vite",
                "build": "tsc && vite build",
                "preview": "vite preview"
            },
            "dependencies": {
                "react": "^18.2.0",
                "react-dom": "^18.2.0"
            },
            "devDependencies": {
                "@types/react": "^18.2.15",
                "@types/react-dom": "^18.2.7", 
                "@vitejs/plugin-react": "^4.0.3",
                "typescript": "^5.0.2",
                "vite": "^4.4.5"
            }
        }
        
        with open(project_dir / "package.json", "w") as f:
            json.dump(package_json, f, indent=2)
        
        # Create tsconfig.json (similar to other projects)
        tsconfig = {
            "compilerOptions": {
                "target": "ES2020",
                "useDefineForClassFields": True,
                "lib": ["ES2020", "DOM", "DOM.Iterable"],
                "module": "ESNext",
                "skipLibCheck": True,
                "moduleResolution": "bundler",
                "allowImportingTsExtensions": True,
                "resolveJsonModule": True,
                "isolatedModules": True,
                "noEmit": True,
                "jsx": "react-jsx",
                "strict": True,
                "noUnusedLocals": True,
                "noUnusedParameters": True,
                "noFallthroughCasesInSwitch": True
            },
            "include": ["src"],
            "references": [{"path": "./tsconfig.node.json"}]
        }
        
        with open(project_dir / "tsconfig.json", "w") as f:
            json.dump(tsconfig, f, indent=2)
        
        # Create vite.config.ts
        vite_config = '''import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
})
'''
        
        with open(project_dir / "vite.config.ts", "w") as f:
            f.write(vite_config)
        
        # Create src directory
        src_dir = project_dir / "src"
        src_dir.mkdir()
        
        # Create App.tsx with CSS modules
        app_tsx = '''import React from 'react'
import './App.css'

function App() {
  return (
    <div className="app">
      <div className="container">
        <h1 className="title">No Tailwind Test Project</h1>
        <p className="subtitle">Testing Palette fallback without Tailwind CSS</p>
        <div className="buttons">
          <button className="btn btn-primary">Primary Button</button>
          <button className="btn btn-secondary">Secondary Button</button>
        </div>
      </div>
    </div>
  )
}

export default App
'''
        
        with open(src_dir / "App.tsx", "w") as f:
            f.write(app_tsx)
        
        # Create App.css with custom styles
        app_css = '''.app {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

.container {
  text-align: center;
  padding: 2rem;
  background: rgba(255, 255, 255, 0.9);
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  backdrop-filter: blur(10px);
  max-width: 600px;
  margin: 2rem;
}

.title {
  font-size: 2.5rem;
  font-weight: 700;
  color: #2d3748;
  margin-bottom: 1rem;
}

.subtitle {
  font-size: 1.25rem;
  color: #4a5568;
  margin-bottom: 2rem;
}

.buttons {
  display: flex;
  gap: 1rem;
  justify-content: center;
  flex-wrap: wrap;
}

.btn {
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 8px;
  font-size: 1rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.btn-primary {
  background: #4299e1;
  color: white;
}

.btn-primary:hover {
  background: #3182ce;
}

.btn-secondary {
  background: #e2e8f0;
  color: #2d3748;
}

.btn-secondary:hover {
  background: #cbd5e0;
}
'''
        
        with open(src_dir / "App.css", "w") as f:
            f.write(app_css)
        
        # Create main.tsx
        main_tsx = '''import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.tsx'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
'''
        
        with open(src_dir / "main.tsx", "w") as f:
            f.write(main_tsx)
        
        # Create index.css
        index_css = '''* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  line-height: 1.6;
  color: #333;
}

#root {
  width: 100%;
  height: 100vh;
}
'''
        
        with open(src_dir / "index.css", "w") as f:
            f.write(index_css)
        
        # Create index.html
        index_html = '''<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>No Tailwind Test Project</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
'''
        
        with open(project_dir / "index.html", "w") as f:
            f.write(index_html)
        
        return project_dir
    
    def generate_project_summary(self, created: List[Dict], failed: List[Dict]):
        """Generate summary of created test projects"""
        summary_path = self.base_dir / "PROJECT_SUMMARY.md"
        
        summary_content = f"""# Palette Test Projects Summary

Generated on: {Path(__file__).name}

## 📋 Overview

This directory contains test projects for validating Palette functionality across different framework setups.

## ✅ Successfully Created Projects ({len(created)})

"""
        
        for project in created:
            summary_content += f"""### {project['name']}
- **Description**: {project['description']}
- **Path**: `{project['path']}`
- **Usage**: Open in VS Code and test Palette generation

"""
        
        if failed:
            summary_content += f"""## ❌ Failed Projects ({len(failed)})

"""
            for project in failed:
                summary_content += f"""### {project['name']}
- **Error**: {project['error']}

"""
        
        summary_content += """## 🧪 Testing Instructions

1. **Open a project in VS Code:**
   ```bash
   code test_projects/vite-react-shadcn
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Test Palette generation:**
   - Press `Ctrl+Shift+P` → "Palette: Open Unified Interface"
   - Try different prompts to test routing:
     - Simple: "Create a button component"
     - Complex: "Create a complete dashboard with charts and tables"

4. **Expected Behavior:**
   - **vite-react-shadcn**: Full Palette functionality with quality validation
   - **next-shadcn**: Next.js framework detection and generation
   - **basic-react**: Fallback without TypeScript
   - **no-tailwind**: Fallback without Tailwind CSS

## 🎯 Test Scenarios by Project

### Vite + React + shadcn/ui (Primary Target)
- ✅ Should detect: Vite, React, TypeScript, Tailwind, shadcn/ui
- ✅ Should route complex requests to Python backend
- ✅ Should apply quality validation
- ✅ Should generate with proper shadcn/ui imports

### Next.js + shadcn/ui  
- ✅ Should detect: Next.js, React, TypeScript, Tailwind
- ✅ Should generate with Next.js patterns
- ✅ Should use proper import paths

### Basic React
- ✅ Should detect: React (no TypeScript)
- ✅ Should generate simpler components
- ✅ Should work without TypeScript features

### No Tailwind
- ✅ Should detect: Vite, React, TypeScript (no Tailwind)
- ✅ Should generate with CSS modules or styled-components
- ✅ Should provide helpful suggestions about Tailwind setup

---

**Next Steps**: Use these projects with the test suites in:
- `test_generation_pipeline.py`
- `test_quality_workflow.py` 
- `test_vscode_integration.py`
- `run_all_tests.py`
"""
        
        with open(summary_path, "w") as f:
            f.write(summary_content)
        
        print(f"📄 Project summary saved: {summary_path}")

def main():
    """Main function to create all test projects"""
    generator = TestProjectGenerator()
    created, failed = generator.create_all_test_projects()
    
    print(f"\n🏁 Test project generation complete!")
    print(f"✅ Created: {len(created)} projects")
    print(f"❌ Failed: {len(failed)} projects")
    
    if created:
        print("\n📁 Created projects:")
        for project in created:
            print(f"   - {project['name']}: {project['path']}")
    
    if failed:
        print("\n⚠️  Failed projects:")
        for project in failed:
            print(f"   - {project['name']}: {project['error']}")
    
    return len(failed) == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)