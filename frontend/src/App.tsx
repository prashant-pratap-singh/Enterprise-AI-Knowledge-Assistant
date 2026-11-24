import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ShieldCheck, MessageSquare, Files, BarChart3, Settings as SettingsIcon } from 'lucide-react';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

export const App: React.FC = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <Router>
        <div className="flex h-screen bg-slate-50 text-slate-800">
          {/* Main App Scaffolding */}
          <aside className="w-64 border-r border-slate-200 bg-white flex flex-col">
            <div className="p-4 border-b border-slate-200 flex items-center space-x-2">
              <ShieldCheck className="w-6 h-6 text-brand-600" />
              <span className="font-semibold text-slate-900 tracking-tight text-sm">Enterprise RAG</span>
            </div>
            <nav className="p-3 space-y-1 flex-1 text-sm font-medium">
              <a href="#chat" className="flex items-center px-3 py-2 rounded-lg bg-brand-50 text-brand-700">
                <MessageSquare className="w-4 h-4 mr-2" />
                Conversations
              </a>
              <a href="#documents" className="flex items-center px-3 py-2 rounded-lg text-slate-600 hover:bg-slate-100">
                <Files className="w-4 h-4 mr-2" />
                Knowledge Base
              </a>
              <a href="#evaluation" className="flex items-center px-3 py-2 rounded-lg text-slate-600 hover:bg-slate-100">
                <BarChart3 className="w-4 h-4 mr-2" />
                Evaluation
              </a>
              <a href="#settings" className="flex items-center px-3 py-2 rounded-lg text-slate-600 hover:bg-slate-100">
                <SettingsIcon className="w-4 h-4 mr-2" />
                Settings
              </a>
            </nav>
            <div className="p-3 border-t border-slate-200 text-xs text-slate-500">
              Workspace: Default Org
            </div>
          </aside>

          {/* Main Content Area */}
          <main className="flex-1 overflow-auto p-8">
            <div className="max-w-4xl mx-auto">
              <h1 className="text-2xl font-bold text-slate-900 mb-2">Enterprise AI Knowledge Assistant</h1>
              <p className="text-slate-600 mb-6">
                Multi-agent orchestrated Retrieval-Augmented Generation with LangGraph and Google Gemini.
              </p>
              <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
                <div className="flex items-center justify-between pb-4 border-b border-slate-100 mb-4">
                  <h2 className="font-semibold text-slate-800">System Ready</h2>
                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                    Phase 1 Scaffolding Complete
                  </span>
                </div>
                <p className="text-sm text-slate-600 leading-relaxed">
                  The frontend is structured with React 18, Vite, TypeScript, Tailwind CSS, TanStack Query, and Axios.
                  All core interfaces, routers, and services are mapped to backend endpoints.
                </p>
              </div>
            </div>
          </main>
        </div>
      </Router>
    </QueryClientProvider>
  );
};

export default App;
