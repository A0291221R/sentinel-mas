import React, { useState, useEffect, useRef } from 'react';
import { Send, LogOut, History, Lightbulb, RefreshCw } from 'lucide-react';

const API_BASE_URL = 'http://localhost:8001'; // Update with your Sentinel API URL

const EXAMPLE_PROMPTS = {
  sop: [
    "How do I escalate a Level-2 anomaly from the Alerts dashboard? What’s the deadline and who to notify?",
    "What are the safe restart steps for Edge-Sentinel on a field device?",
    "How do I acknowledge an alert and mark it False Positive with a note?",
    "Central dashboard is down—what’s the outage procedure and update cadence?",
    "How do I assign an identity to a track using similarity threshold rules?",
    "What is the access revocation process for an offboarded user?",
    "How do I submit model feedback when I see a false positive?",
    "What’s the weekly audit checklist—what logs do I export and review?"
  ],
  events: [
    "Who entered loc-iss-exit-1 on 13-Oct-2025 time between 15:00–18:00 SGT?",
    "Who entered loc-iss-exit-1 from 2025-10-13 15:00–18:30 SGT, only cam01.",
    "How many people visited loc-iss-exit-1 on 13-Oct-2025? Give total and unique visitors.",
    "List anomaly events for loc-iss-exit-1 on 2025-10-13 15:00–18:00, cam01, top 20.",
    "Show entries for Location=loc-iss-exit-1 on 13-Oct-2025 from 15:15–16:00 SGT; include resolved_id if known.",
    "How many unique visitors at loc-iss-exit-1 on 13-Oct-2025 during lunch 15:00–16:00?",
    "List anomaly episodes with incident='anomaly' in loc-iss-exit-1 on 13-Oct-2025 from 15:00–17:30 with confidence.",
    "Who entered loc-iss-exit-1 on 13-Oct-2025 between 15:00–19:00, filtered to cam01?",
  ],
  tracking: [
    "Start tracking resolved_id=id_1760340716573_61ff63dd.",
    "Cancel tracking for resolved_id=id_1760340716573_61ff63dd.",
    "What’s the tracking status of resolved_id=id_1760340716573_61ff63dd?",
    "Start tracking resolved_id=id_1760340716573_61ff63dd and then report status.",
    "Cancel tracking for resolved_id=id_1760340716573_61ff63dd; confirm is_tracked=false.",
    "Check status for resolved_id=id_1760340716573_61ff63dd and show last movement insight.",
    "Start tracking resolved_id=id_1760340716573_61ff63dd; if error, return the server message.",
    "Get status for resolved_id=id_1760340716573_61ff63dd and include the ack_id if available."
  ]
};

export default function SentinelChatbot() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [token, setToken] = useState(null);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loginError, setLoginError] = useState('');
  
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  
  const [queryHistory, setQueryHistory] = useState([]);
  const [showHistory, setShowHistory] = useState(false);
  const [showExamples, setShowExamples] = useState(true);
  const [activeCategory, setActiveCategory] = useState('sop');
  
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    // Check for stored token on mount
    const storedToken = localStorage.getItem('sentinel_token');
    const storedHistory = localStorage.getItem('query_history');
    
    if (storedToken) {
      setToken(storedToken);
      setIsAuthenticated(true);
    }
    
    if (storedHistory) {
      setQueryHistory(JSON.parse(storedHistory));
    }
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoginError('');
    setIsLoading(true);

    try {
      const response = await fetch(`${API_BASE_URL}/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ username, password }),
      });

      if (!response.ok) {
        throw new Error('Invalid credentials');
      }

      const data = await response.json();
      setToken(data.access_token);
      setIsAuthenticated(true);
      localStorage.setItem('sentinel_token', data.access_token);
      setPassword('');
    } catch (error) {
      setLoginError(error.message || 'Login failed. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleLogout = () => {
    setIsAuthenticated(false);
    setToken(null);
    setMessages([]);
    localStorage.removeItem('sentinel_token');
    setUsername('');
  };

  const addToHistory = (query, response) => {
    const newHistory = [
      {
        id: Date.now(),
        query,
        response: response.substring(0, 100) + '...',
        timestamp: new Date().toISOString(),
      },
      ...queryHistory,
    ].slice(0, 20); // Keep only last 20
    
    setQueryHistory(newHistory);
    localStorage.setItem('query_history', JSON.stringify(newHistory));
  };

  const handleSendMessage = async (messageText = input) => {
    if (!messageText.trim() || isLoading) return;

    const userMessage = {
      id: Date.now(),
      role: 'user',
      content: messageText,
      timestamp: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);
    setShowExamples(false);

    try {
      const response = await fetch(`${API_BASE_URL}/api/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({ message: messageText }),
      });

      if (!response.ok) {
        if (response.status === 401) {
          handleLogout();
          throw new Error('Session expired. Please login again.');
        }
        throw new Error('Failed to get response');
      }

      const data = await response.json();
      const assistantMessage = {
        id: Date.now() + 1,
        role: 'assistant',
        content: data.response || data.message || 'No response received',
        timestamp: new Date().toISOString(),
      };

      setMessages((prev) => [...prev, assistantMessage]);
      addToHistory(messageText, assistantMessage.content);
    } catch (error) {
      const errorMessage = {
        id: Date.now() + 1,
        role: 'assistant',
        content: `Error: ${error.message}`,
        timestamp: new Date().toISOString(),
        isError: true,
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleExampleClick = (prompt) => {
    setInput(prompt);
    inputRef.current?.focus();
  };

  const handleHistoryClick = (query) => {
    setInput(query);
    setShowHistory(false);
    inputRef.current?.focus();
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
        <div className="bg-white rounded-lg shadow-xl p-8 w-full max-w-md">
          <div className="text-center mb-8">
            <div className="bg-indigo-600 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
              <span className="text-white text-2xl font-bold">S</span>
            </div>
            <h1 className="text-3xl font-bold text-gray-800">Sentinel Chatbot</h1>
            <p className="text-gray-600 mt-2">Sign in to continue</p>
          </div>

          <form onSubmit={handleLogin} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Username
              </label>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                placeholder="Enter username"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Password
              </label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                placeholder="Enter password"
                required
              />
            </div>

            {loginError && (
              <div className="bg-red-50 text-red-600 px-4 py-2 rounded-lg text-sm">
                {loginError}
              </div>
            )}

            <button
              type="submit"
              disabled={isLoading}
              className="w-full bg-indigo-600 text-white py-2 rounded-lg font-medium hover:bg-indigo-700 transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed"
            >
              {isLoading ? 'Signing in...' : 'Sign In'}
            </button>
          </form>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Sidebar */}
      <div className="w-80 bg-white border-r border-gray-200 flex flex-col">
        {/* Header */}
        <div className="p-4 border-b border-gray-200">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <div className="bg-indigo-600 w-10 h-10 rounded-full flex items-center justify-center">
                <span className="text-white font-bold">S</span>
              </div>
              <div>
                <h2 className="font-semibold text-gray-800">Sentinel</h2>
                <p className="text-xs text-gray-500">{username}</p>
              </div>
            </div>
            <button
              onClick={handleLogout}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
              title="Logout"
            >
              <LogOut size={18} className="text-gray-600" />
            </button>
          </div>

          <div className="flex gap-2">
            <button
              onClick={() => setShowHistory(!showHistory)}
              className={`flex-1 flex items-center justify-center gap-2 px-3 py-2 rounded-lg transition-colors ${
                showHistory
                  ? 'bg-indigo-100 text-indigo-700'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              <History size={16} />
              <span className="text-sm font-medium">History</span>
            </button>
            <button
              onClick={() => setShowExamples(!showExamples)}
              className={`flex-1 flex items-center justify-center gap-2 px-3 py-2 rounded-lg transition-colors ${
                showExamples
                  ? 'bg-indigo-100 text-indigo-700'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              <Lightbulb size={16} />
              <span className="text-sm font-medium">Examples</span>
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto">
          {showHistory ? (
            <div className="p-4">
              <h3 className="font-semibold text-gray-800 mb-3">Recent Queries</h3>
              {queryHistory.length === 0 ? (
                <p className="text-sm text-gray-500 text-center py-8">No history yet</p>
              ) : (
                <div className="space-y-2">
                  {queryHistory.map((item) => (
                    <button
                      key={item.id}
                      onClick={() => handleHistoryClick(item.query)}
                      className="w-full text-left p-3 bg-gray-50 hover:bg-gray-100 rounded-lg transition-colors"
                    >
                      <p className="text-sm font-medium text-gray-800 line-clamp-2">
                        {item.query}
                      </p>
                      <p className="text-xs text-gray-500 mt-1">
                        {new Date(item.timestamp).toLocaleString()}
                      </p>
                    </button>
                  ))}
                </div>
              )}
            </div>
          ) : showExamples ? (
            <div className="p-4">
              <h3 className="font-semibold text-gray-800 mb-3">Example Prompts</h3>
              
              <div className="flex gap-2 mb-4">
                {Object.keys(EXAMPLE_PROMPTS).map((category) => (
                  <button
                    key={category}
                    onClick={() => setActiveCategory(category)}
                    className={`flex-1 px-3 py-2 rounded-lg text-sm font-medium capitalize transition-colors ${
                      activeCategory === category
                        ? 'bg-indigo-600 text-white'
                        : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                    }`}
                  >
                    {category}
                  </button>
                ))}
              </div>

              <div className="space-y-2">
                {EXAMPLE_PROMPTS[activeCategory].map((prompt, index) => (
                  <button
                    key={index}
                    onClick={() => handleExampleClick(prompt)}
                    className="w-full text-left p-3 bg-gray-50 hover:bg-indigo-50 rounded-lg transition-colors border border-transparent hover:border-indigo-200"
                  >
                    <p className="text-sm text-gray-700">{prompt}</p>
                  </button>
                ))}
              </div>
            </div>
          ) : null}
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-6">
          {messages.length === 0 ? (
            <div className="h-full flex items-center justify-center">
              <div className="text-center">
                <div className="bg-indigo-100 w-20 h-20 rounded-full flex items-center justify-center mx-auto mb-4">
                  <Lightbulb size={40} className="text-indigo-600" />
                </div>
                <h2 className="text-2xl font-bold text-gray-800 mb-2">
                  Welcome to Sentinel Chatbot
                </h2>
                <p className="text-gray-600 mb-4">
                  Ask me anything or try one of the example prompts
                </p>
              </div>
            </div>
          ) : (
            <div className="max-w-3xl mx-auto space-y-4">
              {messages.map((message) => (
                <div
                  key={message.id}
                  className={`flex ${
                    message.role === 'user' ? 'justify-end' : 'justify-start'
                  }`}
                >
                  <div
                    className={`max-w-[80%] rounded-lg px-4 py-3 ${
                      message.role === 'user'
                        ? 'bg-indigo-600 text-white'
                        : message.isError
                        ? 'bg-red-50 text-red-800 border border-red-200'
                        : 'bg-white text-gray-800 border border-gray-200'
                    }`}
                  >
                    <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                    <p
                      className={`text-xs mt-1 ${
                        message.role === 'user'
                          ? 'text-indigo-200'
                          : 'text-gray-500'
                      }`}
                    >
                      {new Date(message.timestamp).toLocaleTimeString()}
                    </p>
                  </div>
                </div>
              ))}
              {isLoading && (
                <div className="flex justify-start">
                  <div className="bg-white border border-gray-200 rounded-lg px-4 py-3">
                    <div className="flex items-center gap-2">
                      <RefreshCw size={16} className="text-indigo-600 animate-spin" />
                      <span className="text-sm text-gray-600">Thinking...</span>
                    </div>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        {/* Input Area */}
        <div className="border-t border-gray-200 p-4 bg-white">
          <div className="max-w-3xl mx-auto">
            <div className="flex gap-2">
              <textarea
                ref={inputRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Type your message..."
                className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent resize-none"
                rows="2"
              />
              <button
                onClick={() => handleSendMessage()}
                disabled={isLoading || !input.trim()}
                className="px-6 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors disabled:bg-gray-300 disabled:cursor-not-allowed flex items-center justify-center"
              >
                <Send size={20} />
              </button>
            </div>
            <p className="text-xs text-gray-500 mt-2 text-center">
              Press Enter to send • Shift + Enter for new line
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
