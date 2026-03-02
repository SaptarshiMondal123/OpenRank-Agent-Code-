"use client";

import { useState, useRef, useEffect } from "react";
import ReactMarkdown from "react-markdown";
import Editor from "@monaco-editor/react";
import { 
  Terminal, Cpu, Brain, Send, Bot, Play, Code2, 
  Activity, TrendingUp, CheckCircle, XCircle, LayoutDashboard, Code, Database 
} from "lucide-react";
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip as RechartsTooltip, Legend } from "recharts";

// --- TYPES ---
type Message = {
  role: "user" | "assistant";
  content: string;
};

// --- COLORS FOR CHARTS ---
const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6'];

// ============================================================================
// COMPONENT 1: DASHBOARD VIEW (The Stats)
// ============================================================================
function DashboardView() {
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  // Re-fetch stats every time this view is opened to ensure data is fresh
  useEffect(() => {
    fetch("https://openrank-agent-code.onrender.com/stats")
      .then((res) => res.json())
      .then((data) => {
        setStats(data);
        setLoading(false);
      })
      .catch((err) => {
        console.error(err);
        setLoading(false);
      });
  }, []);

  if (loading) {
    return (
      <div className="h-full flex flex-col items-center justify-center text-slate-500 gap-4">
        <div className="w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
        <p className="font-mono text-sm animate-pulse">SYNCING METRICS...</p>
      </div>
    );
  }

  return (
    <div className="h-full overflow-y-auto p-8 bg-[#0f172a] custom-scrollbar">
      <div className="max-w-6xl mx-auto space-y-8">
        
        {/* Top Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-[#1e293b] p-6 rounded-xl border border-slate-700 shadow-lg">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-blue-500/20 rounded-full text-blue-400">
                <Activity className="w-8 h-8" />
              </div>
              <div>
                <p className="text-xs text-slate-400 uppercase font-bold tracking-wider">Total Submissions</p>
                <p className="text-3xl font-bold text-white mt-1">{stats.total}</p>
              </div>
            </div>
          </div>

          <div className="bg-[#1e293b] p-6 rounded-xl border border-slate-700 shadow-lg">
            <div className="flex items-center gap-4">
              <div className={`p-3 rounded-full ${stats.pass_rate > 50 ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'}`}>
                <TrendingUp className="w-8 h-8" />
              </div>
              <div>
                <p className="text-xs text-slate-400 uppercase font-bold tracking-wider">Win Rate</p>
                <p className="text-3xl font-bold text-white mt-1">{stats.pass_rate}%</p>
              </div>
            </div>
          </div>

          <div className="bg-[#1e293b] p-6 rounded-xl border border-slate-700 shadow-lg flex items-center justify-center">
             <div className="text-center">
                <p className="text-xs text-slate-400 font-bold mb-2 uppercase tracking-wider">Dominant Style</p>
                <span className="text-lg text-white font-mono bg-slate-800 px-4 py-1.5 rounded-full border border-slate-600">
                  {stats.patterns.length > 0 ? stats.patterns.sort((a:any,b:any) => b.value - a.value)[0].name : "N/A"}
                </span>
             </div>
          </div>
        </div>

        {/* Charts & History Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          
          {/* Pie Chart */}
          <div className="bg-[#1e293b] p-6 rounded-xl border border-slate-700 shadow-lg flex flex-col h-[450px]">
            <h2 className="text-lg font-bold text-white mb-6 flex items-center gap-2">
              <Brain className="w-5 h-5 text-purple-400"/> Pattern Distribution
            </h2>
            <div className="flex-1 w-full min-h-0">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={stats.patterns}
                    cx="50%"
                    cy="50%"
                    innerRadius={80}
                    outerRadius={120}
                    fill="#8884d8"
                    paddingAngle={5}
                    dataKey="value"
                    stroke="none"
                  >
                    {stats.patterns.map((entry: any, index: number) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <RechartsTooltip 
                    contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', color: '#fff' }}
                    itemStyle={{ color: '#fff' }}
                  />
                  <Legend verticalAlign="bottom" height={36} iconType="circle"/>
                </PieChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Recent Activity Table */}
          <div className="bg-[#1e293b] p-6 rounded-xl border border-slate-700 shadow-lg flex flex-col h-[450px]">
            <h2 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
              <Code className="w-5 h-5 text-blue-400"/> Recent Activity
            </h2>
            <div className="overflow-auto flex-1 custom-scrollbar pr-2">
              <table className="w-full text-left border-collapse">
                <thead className="sticky top-0 bg-[#1e293b] z-10 shadow-sm">
                  <tr className="text-slate-400 text-xs uppercase tracking-wider border-b border-slate-700">
                    <th className="pb-3 pl-2 font-semibold">Status</th>
                    <th className="pb-3 font-semibold">Problem</th>
                    <th className="pb-3 font-semibold hidden sm:table-cell">Complexity</th>
                    <th className="pb-3 text-right pr-2 font-semibold">Date</th>
                  </tr>
                </thead>
                <tbody className="text-sm divide-y divide-slate-700/50">
                  {stats.recent.map((item: any) => (
                    <tr key={item.id} className="hover:bg-slate-800/50 transition-colors group">
                      <td className="py-3 pl-2 align-middle">
                        {item.status === "PASS" ? (
                          <div className="flex items-center gap-2">
                             <CheckCircle className="w-4 h-4 text-green-500" />
                          </div>
                        ) : (
                          <div className="flex items-center gap-2">
                             <XCircle className="w-4 h-4 text-red-500" />
                          </div>
                        )}
                      </td>
                      <td className="py-3 align-middle">
                        <p className="font-medium text-slate-200 truncate max-w-[150px]" title={item.problem}>
                          {item.problem}
                        </p>
                      </td>
                      <td className="py-3 align-middle hidden sm:table-cell">
                          <div className="flex flex-col">
                             <span className="text-xs font-mono text-blue-300">{item.complexity}</span>
                             <span className="text-[10px] text-slate-500">{item.space}</span>
                          </div>
                      </td>
                      <td className="py-3 text-right text-slate-500 pr-2 align-middle text-xs font-mono">{item.date}</td>
                    </tr>
                  ))}
                  {stats.recent.length === 0 && (
                    <tr>
                      <td colSpan={4} className="text-center py-12 text-slate-500 italic">No recent activity found</td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>

        </div>
      </div>
    </div>
  );
}

// ============================================================================
// COMPONENT 2: WORKSPACE VIEW (Editor + Chat)
// ============================================================================
function WorkspaceView({ onRunComplete }: { onRunComplete: () => void }) {
  // --- STATE ---
  const [problemsList, setProblemsList] = useState<any[]>([]);
  const [selectedProblem, setSelectedProblem] = useState<any>(null);
  
  const [code, setCode] = useState("");
  const [problemContext, setProblemContext] = useState(""); // Sent to the AI
  
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [chatLoading, setChatLoading] = useState(false);
  const [judgeResults, setJudgeResults] = useState<any[]>([]);

  const chatEndRef = useRef<HTMLDivElement>(null);

  // --- 1. LOAD PROBLEMS ON STARTUP ---
  useEffect(() => {
    fetch("https://openrank-agent-code.onrender.com/problems")
      .then(res => res.json())
      .then(data => {
        if (data.problems) setProblemsList(data.problems);
      })
      .catch(console.error);
  }, []);

  // Scroll chat to bottom
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // --- 2. HANDLE PROBLEM SELECTION ---
  const handleProblemChange = async (e: React.ChangeEvent<HTMLSelectElement>) => {
    const problemId = e.target.value;
    if (!problemId) return;
    
    // Fetch full problem details
    try {
      const res = await fetch(`https://openrank-agent-code.onrender.com/problems/${problemId}`);
      const data = await res.json();
      
      setSelectedProblem(data);
      setCode(data.starter_code || "");
      setProblemContext(`${data.title}: ${data.description}`);
      setJudgeResults([]); // Clear old test results
      setMessages([]); // Clear old chat
    } catch (err) {
      console.error(err);
    }
  };

  // --- 3. EXECUTION FUNCTIONS ---
  const runCodeOnly = async () => {
    if (!selectedProblem) return alert("Please select a problem first!");
    setLoading(true);
    setJudgeResults([]); 
    
    try {
      const res = await fetch("https://openrank-agent-code.onrender.com/full-critique", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        // Notice we send the title so the backend can find the test cases!
        body: JSON.stringify({ code, problem: selectedProblem.title, language: "python", run_ai: false }),
      });
      const data = await res.json();
      if (data.judge_results) setJudgeResults(data.judge_results);
      setTimeout(() => onRunComplete(), 500);
    } catch (error) {
      console.error(error);
    }
    setLoading(false);
  };

  const askAiCoach = async () => {
    if (!selectedProblem) return alert("Please select a problem first!");
    setChatLoading(true);
    setMessages([]); 
    
    try {
      const res = await fetch("https://openrank-agent-code.onrender.com/full-critique", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ code, problem: selectedProblem.title, language: "python", run_ai: true }),
      });
      const data = await res.json();
      
      setMessages([{ role: "assistant", content: data.report }]);
      if (data.judge_results && data.judge_results.length > 0) {
          setJudgeResults(data.judge_results);
      }
    } catch (error) {
      setMessages([{ role: "assistant", content: "⚠️ Error connecting to the Coach." }]);
    }
    setChatLoading(false);
  };

  const sendMessage = async () => {
    if (!input.trim()) return;
    const newMsg: Message = { role: "user", content: input };
    const updatedHistory = [...messages, newMsg];
    
    setMessages(updatedHistory);
    setInput("");
    setChatLoading(true);

    try {
      const res = await fetch("https://openrank-agent-code.onrender.com/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ code, problem: selectedProblem.title, history: updatedHistory }),
      });
      const data = await res.json();
      setMessages([...updatedHistory, { role: "assistant", content: data.reply }]);
    } catch (error) {
      console.error(error);
    }
    setChatLoading(false);
  };

  return (
    <div className="flex-1 flex h-full overflow-hidden">
      
      {/* PANE 1: PROBLEM DESCRIPTION (LEFT) */}
      <div className="w-[350px] flex flex-col border-r border-slate-800 bg-[#0f172a]">
        <div className="p-4 border-b border-slate-800 bg-[#1e293b]">
          <select 
            onChange={handleProblemChange}
            className="w-full bg-[#0f172a] border border-slate-700 text-white text-sm rounded-lg px-3 py-2.5 outline-none focus:border-blue-500 transition-colors cursor-pointer font-semibold"
            defaultValue=""
          >
            <option value="" disabled>📚 Select a Problem...</option>
            {problemsList.map((p) => (
              <option key={p.id} value={p.id}>
                {p.title}
              </option>
            ))}
          </select>
        </div>

        <div className="flex-1 overflow-y-auto p-6 custom-scrollbar">
          {selectedProblem ? (
            <div className="space-y-4">
              <div className="flex items-center gap-3 mb-2">
                <h2 className="text-2xl font-bold text-white">{selectedProblem.title}</h2>
              </div>
              <div className="flex items-center gap-2 mb-6">
                <span className={`px-2.5 py-1 rounded-full text-xs font-bold bg-slate-800/80 border
                  ${selectedProblem.difficulty === 'Easy' ? 'text-emerald-400 border-emerald-900' : 
                    selectedProblem.difficulty === 'Medium' ? 'text-amber-400 border-amber-900' : 
                    'text-red-400 border-red-900'}`}>
                  {selectedProblem.difficulty}
                </span>
              </div>
              
              <div className="prose prose-invert prose-sm max-w-none text-slate-300 leading-relaxed">
                <ReactMarkdown>{selectedProblem.description}</ReactMarkdown>
              </div>
            </div>
          ) : (
            <div className="h-full flex flex-col items-center justify-center text-slate-600 opacity-60 text-center space-y-4">
              <Database className="w-12 h-12" />
              <p className="text-sm px-4">Select a problem from the dropdown to view its description and load the starter code.</p>
            </div>
          )}
        </div>
      </div>

      {/* PANE 2: EDITOR & EXECUTION (MIDDLE) */}
      <div className="flex-1 flex flex-col h-full min-w-[400px] border-r border-slate-800 bg-[#1e293b]">
        
        {/* Editor Area: flex-1 takes remaining space, min-h-0 absolutely forces it to not overflow */}
        <div className="flex-1 relative min-h-0">
          <Editor
            height="100%"
            defaultLanguage="python"
            value={code}
            theme="vs-dark"
            onChange={(value) => setCode(value || "")}
            options={{
                minimap: { enabled: false },
                fontSize: 14,
                lineNumbers: "on",
                scrollBeyondLastLine: false,
                automaticLayout: true,
                padding: { top: 20, bottom: 20 },
            }}
          />
          <div className="absolute bottom-6 right-6 flex items-center gap-3 z-50">
            <button
              onClick={runCodeOnly}
              disabled={loading || chatLoading || !selectedProblem}
              className={`px-6 py-3 rounded-full font-bold shadow-xl flex items-center gap-2 transition-all transform hover:scale-105 active:scale-95
                ${loading || !selectedProblem ? "bg-slate-700 cursor-not-allowed text-slate-400" : "bg-emerald-600 hover:bg-emerald-500 text-white"}`}
            >
              {loading ? <Cpu className="animate-spin w-5 h-5" /> : <Play className="w-5 h-5 fill-current" />}
              {loading ? "Running..." : "Run Code"}
            </button>

            <button
              onClick={askAiCoach}
              disabled={loading || chatLoading || !selectedProblem}
              className={`px-6 py-3 rounded-full font-bold shadow-xl flex items-center gap-2 transition-all transform hover:scale-105 active:scale-95
                ${chatLoading || !selectedProblem ? "bg-slate-700 cursor-not-allowed text-slate-400" : "bg-blue-600 hover:bg-blue-500 text-white"}`}
            >
              {chatLoading ? <Brain className="animate-spin w-5 h-5" /> : <Bot className="w-5 h-5" />}
              {chatLoading ? "Analyzing..." : "Get AI Feedback"}
            </button>
          </div>
        </div>

        {/* EXECUTION RESULTS PANEL: shrink-0 ensures it NEVER gets crushed by the editor */}
        {judgeResults.length > 0 && (
          <div className="h-64 shrink-0 bg-[#0f172a] border-t border-slate-700 overflow-y-auto p-4 z-40 relative custom-scrollbar">
            <h3 className="text-white font-bold mb-4 flex items-center gap-2">
              🧪 Execution Results
            </h3>
            <div className="flex flex-col gap-4">
              {judgeResults.map((result, index) => (
                <div 
                  key={index} 
                  className={`p-4 rounded-lg border ${
                    result.passed ? "bg-emerald-900/20 border-emerald-800" : "bg-red-900/20 border-red-800"
                  }`}
                >
                  <div className="flex items-center justify-between mb-3">
                    <div className="font-bold flex items-center gap-2">
                      {result.passed ? (
                        <span className="text-emerald-400">✅ Case {index + 1} Passed</span>
                      ) : (
                        <span className="text-red-400">❌ Case {index + 1} Failed</span>
                      )}
                    </div>
                    
                    {result.passed && result.runtime > 0 && (
                      <div className="flex items-center gap-3 text-xs font-mono font-medium opacity-80">
                        <span className="flex items-center gap-1 bg-slate-800/80 px-2 py-1 rounded text-blue-300 border border-slate-700">
                          <Cpu className="w-3 h-3" /> {result.runtime} ms
                        </span>
                        <span className="flex items-center gap-1 bg-slate-800/80 px-2 py-1 rounded text-purple-300 border border-slate-700">
                          <Database className="w-3 h-3" /> {result.memory} MB
                        </span>
                      </div>
                    )}
                  </div>

                  <div className="text-sm font-mono space-y-2">
                    <div className="bg-[#1e293b] p-2 rounded text-slate-300">
                      <span className="text-slate-500 select-none">Input:    </span> {result.input}
                    </div>
                    <div className="bg-[#1e293b] p-2 rounded text-slate-300">
                      <span className="text-slate-500 select-none">Expected: </span> {result.expected}
                    </div>
                    <div className={`p-2 rounded ${result.passed ? "bg-[#1e293b] text-slate-300" : "bg-red-950 text-red-300"}`}>
                      <span className="text-slate-500 select-none">Actual:   </span> {result.actual}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* PANE 3: AI COACH CHAT (RIGHT) */}
      <div className="w-[400px] bg-[#0f172a] flex flex-col h-full shrink-0">
        
        {/* Header: shrink-0 */}
        <div className="bg-slate-900/50 px-4 py-3 border-b border-slate-800 flex items-center gap-2 shrink-0">
          <Bot className="w-4 h-4 text-blue-400" />
          <h2 className="font-bold text-slate-200 text-xs tracking-wider uppercase">AI Coach Intelligence</h2>
        </div>
        
        {/* Chat Log: flex-1 + min-h-0 creates a perfect boundary for the scrollbar */}
        <div className="flex-1 min-h-0 overflow-y-auto p-4 space-y-6 scroll-smooth custom-scrollbar">
          {messages.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center text-slate-600 opacity-60 space-y-4">
              <Terminal className="w-12 h-12" />
              <p className="text-sm text-center px-4">Run the code or ask for feedback to summon the AI Coach.</p>
            </div>
          ) : (
            messages.map((msg, idx) => (
              <div key={idx} className={`flex gap-3 ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
                {msg.role === "assistant" && (
                  <div className="w-6 h-6 rounded bg-blue-600/20 flex items-center justify-center shrink-0 mt-1">
                    <Bot className="w-3.5 h-3.5 text-blue-400" />
                  </div>
                )}
                <div className={`max-w-[85%] rounded-lg px-4 py-3 text-sm leading-relaxed break-words
                  ${msg.role === "user" ? "bg-slate-700 text-white" : "bg-[#1e293b] text-slate-300 border border-slate-700/50"}`}>
                  <ReactMarkdown 
                    components={{
                      code: ({node, ...props}) => <code className="bg-black/30 rounded px-1 py-0.5 text-orange-300 font-mono text-xs whitespace-pre-wrap break-words" {...props} />
                    }}
                  >
                    {msg.content}
                  </ReactMarkdown>
                </div>
              </div>
            ))
          )}
          {chatLoading && (
             <div className="flex gap-3 animate-pulse">
                <div className="w-6 h-6 rounded bg-blue-600/20 flex items-center justify-center">...</div>
                <div className="bg-[#1e293b] rounded-lg px-4 py-3 text-sm text-slate-500">Thinking...</div>
             </div>
          )}
          <div ref={chatEndRef} />
        </div>

        {/* Input Bar: shrink-0 */}
        <div className="p-4 bg-slate-900 border-t border-slate-800 shrink-0">
          <div className="relative">
            <input
              type="text"
              className="w-full bg-[#1e293b] text-white rounded-lg pl-4 pr-12 py-3 text-sm border border-slate-700 focus:border-blue-500 focus:outline-none transition-all placeholder:text-slate-600"
              placeholder="Ask for hints..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && sendMessage()}
              disabled={!selectedProblem}
            />
            <button 
              onClick={sendMessage}
              disabled={!input.trim() || chatLoading || !selectedProblem}
              className="absolute right-2 top-1.5 p-1.5 bg-blue-600 hover:bg-blue-500 text-white rounded-md transition-all disabled:opacity-0 disabled:cursor-not-allowed"
            >
              <Send className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

    </div>
  );
}

// ============================================================================
// MAIN COMPONENT: APP SHELL
// ============================================================================
export default function Home() {
  const [activeTab, setActiveTab] = useState<"workspace" | "dashboard">("workspace");
  const [refreshTrigger, setRefreshTrigger] = useState(0);

  return (
    <div className="h-screen bg-[#0f172a] text-slate-300 font-sans flex flex-col overflow-hidden">
      {/* HEADER */}
      <header className="h-16 border-b border-slate-800 flex items-center px-6 bg-[#0f172a] justify-between shrink-0">
        <div className="flex items-center gap-8">
          {/* Logo */}
          <div className="flex items-center gap-3">
            <div className="bg-blue-600 p-2 rounded-lg">
               <Brain className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className="text-lg font-bold text-white tracking-tight leading-none">OpenRank</h1>
              <p className="text-[10px] text-slate-500 font-mono">AI PLATFORM</p>
            </div>
          </div>

          {/* Navigation Tabs */}
          <nav className="flex bg-[#1e293b] p-1 rounded-lg border border-slate-700/50">
            <button
              onClick={() => setActiveTab("workspace")}
              className={`flex items-center gap-2 px-4 py-1.5 rounded-md text-xs font-bold transition-all
                ${activeTab === "workspace" 
                  ? "bg-blue-600 text-white shadow-lg" 
                  : "text-slate-400 hover:text-slate-200 hover:bg-slate-700/50"}`}
            >
              <Code2 className="w-4 h-4" /> Workspace
            </button>
            <button
              onClick={() => setActiveTab("dashboard")}
              className={`flex items-center gap-2 px-4 py-1.5 rounded-md text-xs font-bold transition-all
                ${activeTab === "dashboard" 
                  ? "bg-blue-600 text-white shadow-lg" 
                  : "text-slate-400 hover:text-slate-200 hover:bg-slate-700/50"}`}
            >
              <LayoutDashboard className="w-4 h-4" /> My Performance
            </button>
          </nav>
        </div>

        <div className="flex gap-4 items-center">
             <span className="text-xs font-mono text-slate-500">v1.0.0</span>
             <div className="w-8 h-8 rounded-full bg-slate-700 flex items-center justify-center text-xs font-bold text-white">SM</div>
        </div>
      </header>
      
      {/* CONTENT AREA */}
      <main className="flex-1 overflow-hidden relative">
        {activeTab === "workspace" ? (
          <WorkspaceView onRunComplete={() => setRefreshTrigger(prev => prev + 1)} />
        ) : (
          <DashboardView key={refreshTrigger} />
        )}
      </main>
    </div>
  );
}