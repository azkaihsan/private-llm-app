const now = Date.now();
const hour = 3600000;
const day = 86400000;

export const models = [
  { id: 'llama3.1:70b', name: 'llama3.1:70b', size: '39 GB', provider: 'Ollama' },
  { id: 'gpt-4o', name: 'GPT-4o', size: '', provider: 'OpenAI' },
  { id: 'gpt-4o-mini', name: 'GPT-4o mini', size: '', provider: 'OpenAI' },
  { id: 'claude-3.5-sonnet', name: 'Claude 3.5 Sonnet', size: '', provider: 'Anthropic' },
  { id: 'mistral-large', name: 'Mistral Large', size: '', provider: 'Mistral' },
  { id: 'gemma2:27b', name: 'gemma2:27b', size: '15 GB', provider: 'Ollama' },
  { id: 'phi3:14b', name: 'phi3:14b', size: '7.9 GB', provider: 'Ollama' },
  { id: 'codellama:34b', name: 'codellama:34b', size: '19 GB', provider: 'Ollama' },
  { id: 'deepseek-coder:33b', name: 'deepseek-coder:33b', size: '18 GB', provider: 'Ollama' },
];

export const initialChats = [
  {
    id: 'chat-1',
    title: 'Explain quantum computing basics',
    model: 'llama3.1:70b',
    createdAt: now - 2 * hour,
    messages: [
      { id: 'msg-1', role: 'user', content: 'Can you explain quantum computing in simple terms?', timestamp: now - 2 * hour },
      { id: 'msg-2', role: 'assistant', content: 'Quantum computing is a type of computation that harnesses quantum mechanical phenomena like **superposition** and **entanglement** to process information in fundamentally different ways than classical computers.\n\nHere are the key concepts:\n\n1. **Qubits**: Unlike classical bits (0 or 1), quantum bits can exist in a superposition of both states simultaneously\n2. **Superposition**: A qubit can be in multiple states at once until measured\n3. **Entanglement**: Qubits can be correlated so that the state of one instantly influences the other\n4. **Quantum Gates**: Operations that manipulate qubits, similar to logic gates in classical computing\n\n```python\n# Simple quantum circuit example (Qiskit)\nfrom qiskit import QuantumCircuit\n\nqc = QuantumCircuit(2, 2)\nqc.h(0)        # Hadamard gate - creates superposition\nqc.cx(0, 1)    # CNOT gate - creates entanglement\nqc.measure([0,1], [0,1])\n```\n\nQuantum computers excel at specific tasks like:\n- **Cryptography**: Breaking current encryption methods\n- **Drug Discovery**: Simulating molecular interactions\n- **Optimization**: Solving complex optimization problems\n- **Machine Learning**: Accelerating certain ML algorithms', timestamp: now - 2 * hour + 5000 },
    ],
  },
  {
    id: 'chat-2',
    title: 'Python async/await best practices',
    model: 'gpt-4o',
    createdAt: now - 5 * hour,
    messages: [
      { id: 'msg-3', role: 'user', content: 'What are the best practices for using async/await in Python?', timestamp: now - 5 * hour },
      { id: 'msg-4', role: 'assistant', content: 'Here are the best practices for using **async/await** in Python:\n\n## 1. Use asyncio.run() as entry point\n\n```python\nimport asyncio\n\nasync def main():\n    await some_async_function()\n\nasyncio.run(main())\n```\n\n## 2. Gather concurrent tasks\n\n```python\nasync def fetch_all():\n    tasks = [fetch_url(url) for url in urls]\n    results = await asyncio.gather(*tasks)\n    return results\n```\n\n## 3. Use async context managers\n\n```python\nasync with aiohttp.ClientSession() as session:\n    async with session.get(url) as response:\n        data = await response.json()\n```\n\n## Key Tips:\n- Never mix sync and async code without proper bridging\n- Use `asyncio.create_task()` for fire-and-forget tasks\n- Always handle exceptions in async functions\n- Use `asyncio.Semaphore` to limit concurrency', timestamp: now - 5 * hour + 5000 },
    ],
  },
  {
    id: 'chat-3',
    title: 'React hooks best practices',
    model: 'claude-3.5-sonnet',
    createdAt: now - 1 * day - 3 * hour,
    messages: [
      { id: 'msg-5', role: 'user', content: 'Can you share some React hooks best practices?', timestamp: now - 1 * day - 3 * hour },
      { id: 'msg-6', role: 'assistant', content: 'Here are essential **React Hooks best practices**:\n\n## Custom Hooks\n\nExtract reusable logic into custom hooks:\n\n```jsx\nfunction useLocalStorage(key, initialValue) {\n  const [value, setValue] = useState(() => {\n    const stored = localStorage.getItem(key);\n    return stored ? JSON.parse(stored) : initialValue;\n  });\n\n  useEffect(() => {\n    localStorage.setItem(key, JSON.stringify(value));\n  }, [key, value]);\n\n  return [value, setValue];\n}\n```\n\n## Key Rules:\n1. **Don\'t call hooks conditionally** - always at the top level\n2. **Use useCallback for event handlers** passed to child components\n3. **Use useMemo for expensive computations**\n4. **Keep effects focused** - one effect per concern\n5. **Clean up effects** - return cleanup functions when needed', timestamp: now - 1 * day - 3 * hour + 5000 },
    ],
  },
  {
    id: 'chat-4',
    title: 'Docker containerization guide',
    model: 'llama3.1:70b',
    createdAt: now - 3 * day,
    messages: [
      { id: 'msg-7', role: 'user', content: 'How do I containerize a Node.js application with Docker?', timestamp: now - 3 * day },
      { id: 'msg-8', role: 'assistant', content: 'Here\'s a complete guide to containerize a **Node.js application** with Docker:\n\n## 1. Create a Dockerfile\n\n```dockerfile\nFROM node:20-alpine\nWORKDIR /app\nCOPY package*.json ./\nRUN npm ci --only=production\nCOPY . .\nEXPOSE 3000\nCMD ["node", "server.js"]\n```\n\n## 2. Create .dockerignore\n\n```\nnode_modules\nnpm-debug.log\n.git\n.env\n```\n\n## 3. Build and run\n\n```bash\ndocker build -t my-node-app .\ndocker run -p 3000:3000 my-node-app\n```\n\n## Best Practices:\n- Use multi-stage builds for smaller images\n- Run as non-root user\n- Use specific version tags\n- Leverage build cache with proper COPY ordering', timestamp: now - 3 * day + 5000 },
    ],
  },
  {
    id: 'chat-5',
    title: 'Machine learning model selection',
    model: 'gpt-4o-mini',
    createdAt: now - 10 * day,
    messages: [
      { id: 'msg-9', role: 'user', content: 'How do I choose the right machine learning model for my project?', timestamp: now - 10 * day },
      { id: 'msg-10', role: 'assistant', content: 'Choosing the right ML model depends on several factors:\n\n## Decision Framework\n\n| Factor | Consider |\n|--------|----------|\n| Data size | Small → simpler models, Large → deep learning |\n| Task type | Classification, Regression, Clustering |\n| Interpretability | Need to explain? → Linear models, Trees |\n| Speed | Real-time? → Lightweight models |\n\n## Common Choices:\n1. **Tabular data**: XGBoost, Random Forest\n2. **Images**: CNNs (ResNet, EfficientNet)\n3. **Text**: Transformers (BERT, GPT)\n4. **Time series**: LSTM, Prophet\n5. **Recommendations**: Collaborative filtering\n\nAlways start simple and iterate!', timestamp: now - 10 * day + 5000 },
    ],
  },
];

export const suggestions = [
  { title: 'Help me study', subtitle: 'vocabulary for a college entrance exam' },
  { title: 'Give me ideas', subtitle: "for what to do with my kids' art" },
  { title: 'Tell me a fun fact', subtitle: 'about the Roman Empire' },
  { title: 'Create a workout', subtitle: 'plan for a beginner' },
];

export const mockResponses = [
  "That's a great question! Let me break it down for you...\n\nThe key thing to understand is that this concept builds on several foundational ideas. Let me walk you through each one:\n\n1. **First principle**: Understanding the basics is crucial before moving to advanced topics\n2. **Building blocks**: Each component serves a specific purpose in the larger system\n3. **Integration**: Everything works together seamlessly when properly configured\n\n```python\n# Example implementation\ndef solve(problem):\n    analysis = analyze(problem)\n    solution = optimize(analysis)\n    return solution\n```\n\nWould you like me to elaborate on any of these points?",
  "Here's what I found:\n\n## Overview\n\nThis is a fascinating topic with many dimensions. Let me share the most important aspects:\n\n- **Key insight**: The fundamental mechanism is well-understood in the literature\n- **Practical application**: You can apply this in several real-world scenarios\n- **Common pitfalls**: Watch out for these common mistakes that beginners make\n\nThe best approach is to start with a solid foundation and build from there. I'd recommend the following steps:\n\n1. Study the fundamentals thoroughly\n2. Practice with small examples\n3. Gradually increase complexity\n4. Review and refine your understanding\n\nLet me know if you'd like more details on any specific aspect!",
  "Great question! Here's a comprehensive answer:\n\nThe short answer is that it depends on your specific use case. However, here are some general guidelines:\n\n1. **Start simple** - Don't overcomplicate things from the beginning\n2. **Measure first** - Get baseline metrics before attempting to optimize\n3. **Iterate** - Make incremental improvements based on data\n4. **Test thoroughly** - Validate your assumptions at every step\n\n```javascript\n// Quick example\nconst approach = (problem) => {\n  const baseline = measure(problem);\n  const improved = optimize(baseline);\n  return validate(improved);\n};\n```\n\nIn practice, most people find that approach #1 works best for their needs. The key is to remain flexible and adapt as you learn more about the problem space.\n\nWould you like me to go deeper into any of these areas?",
];
