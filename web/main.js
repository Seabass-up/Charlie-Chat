// Charlie Web UI - Enhanced Frontend with Rich Text and Controls
(function () {
  const el = (sel) => document.querySelector(sel);
  const container = el('#message-container');
  const input = el('#user-input');
  const sendBtn = el('#send-button');

  // Core UI state
  let isSending = false;
  let voiceEnabled = false;
  let isListening = false;
  let recognition = null;
  let currentModel = 'gpt-oss:120b';

  // File browser state
  let currentPath = "C:\\Users\\seaba\\CascadeProjects\\Charlie";
  let fileBrowserCollapsed = false;

  // Initialize rich text renderer
  marked.setOptions({
    highlight: function(code, language) {
      const validLanguage = hljs.getLanguage(language) ? language : 'plaintext';
      return hljs.highlight(code, { language: validLanguage }).value;
    },
    breaks: true,
    gfm: true
  });

  function scrollToBottom() {
    container.scrollTop = container.scrollHeight;
  }

  function timeNow() {
    const d = new Date();
    return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  }

  function createTyping() {
    const typing = document.createElement('span');
    typing.className = 'typing';
    typing.innerHTML = '<span class="dot"></span><span class="dot"></span><span class="dot"></span>';
    return typing;
  }

  function renderRichText(text) {
    // Parse markdown with marked
    const html = marked.parse(text);
    return html;
  }

  // File browser functions
  async function loadFileList(path = currentPath) {
    try {
      const response = await fetch(`/api/files?path=${encodeURIComponent(path)}`);
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      const data = await response.json();

      currentPath = data.path;
      el('#current-path').textContent = currentPath;

      const fileList = el('#file-list');
      fileList.innerHTML = '';

      data.items.forEach(item => {
        const fileItem = document.createElement('div');
        fileItem.className = `file-item file-type-${item.type}`;
        fileItem.onclick = () => handleFileClick(item);

        const icon = item.type === 'directory' ? '📁' : '📄';
        const size = item.type === 'file' && item.size ? formatFileSize(item.size) : '';

        fileItem.innerHTML = `
          <span class="file-icon">${icon}</span>
          <span class="file-name">${item.name}</span>
          <span class="file-size">${size}</span>
        `;

        fileList.appendChild(fileItem);
      });

    } catch (error) {
      console.error('Error loading file list:', error);
      addMessage('charlie', `Error loading files: ${error.message}`);
    }
  }

  function formatFileSize(bytes) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
  }

  async function handleFileClick(item) {
    if (item.type === 'directory') {
      await loadFileList(item.path);
    } else {
      // Read file content
      try {
        const response = await fetch(`/api/files/read?path=${encodeURIComponent(item.path)}`);
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }
        const data = await response.json();

        let content = data.content;
        if (data.truncated) {
          content += `\n\n--- File truncated (${data.total_lines} total lines, showing first ${data.shown_lines}) ---`;
        }

        // Format file content for chat
        const fileMessage = `📄 **${item.name}**\n\n\`\`\`\n${content}\n\`\`\``;
        addMessage('user', `Show me the contents of ${item.name}`);
        sendMessage(fileMessage);

      } catch (error) {
        console.error('Error reading file:', error);
        addMessage('charlie', `Error reading file ${item.name}: ${error.message}`);
      }
    }
  }

  function toggleFileBrowser() {
    const content = el('#file-browser-content');
    const toggleBtn = el('#toggle-file-browser');

    fileBrowserCollapsed = !fileBrowserCollapsed;

    if (fileBrowserCollapsed) {
      content.classList.add('collapsed');
      toggleBtn.textContent = '▶️';
    } else {
      content.classList.remove('collapsed');
      toggleBtn.textContent = '◀️';
    }
  }

  function goUpDirectory() {
    const pathParts = currentPath.split('\\');
    if (pathParts.length > 1) {
      const parentPath = pathParts.slice(0, -1).join('\\');
      loadFileList(parentPath);
    }
  }

  function addMessage(role, text, isHtml = false) {
    const wrap = document.createElement('div');
    wrap.className = `message ${role}`;

    const avatar = document.createElement('div');
    avatar.className = 'avatar';

    const bubble = document.createElement('div');
    bubble.className = 'bubble';

    if (isHtml) {
      bubble.innerHTML = text;
    } else {
      bubble.textContent = text;
    }

    const meta = document.createElement('div');
    meta.className = 'meta';
    meta.textContent = `${role === 'user' ? 'You' : 'Charlie'} • ${timeNow()}`;

    wrap.appendChild(avatar);
    const bubbleWrap = document.createElement('div');
    bubbleWrap.appendChild(bubble);
    bubbleWrap.appendChild(meta);
    wrap.appendChild(bubbleWrap);

    container.appendChild(wrap);
    scrollToBottom();

    // Apply syntax highlighting to any code blocks
    if (isHtml) {
      wrap.querySelectorAll('pre code').forEach((block) => {
        hljs.highlightElement(block);
      });
    }

    return wrap;
  }

  function addTyping(role = 'charlie') {
    const wrap = document.createElement('div');
    wrap.className = `message ${role}`;

    const avatar = document.createElement('div');
    avatar.className = 'avatar';

    const bubble = document.createElement('div');
    bubble.className = 'bubble';
    bubble.appendChild(createTyping());

    wrap.appendChild(avatar);
    wrap.appendChild(bubble);
    container.appendChild(wrap);
    scrollToBottom();
    return wrap;
  }

  async function sendMessage(messageText = null) {
    if (isSending) return;
    const text = messageText || input.value.trim();
    if (!text) return;

    if (!messageText) {
      input.value = '';
    }

    addMessage('user', text);
    const typingEl = addTyping('charlie');
    isSending = true;

    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: text,
          model: currentModel
        })
      });

      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();

      typingEl.remove();

      if (data.reply) {
        // Render rich text response
        const html = renderRichText(data.reply);
        addMessage('charlie', html, true);
      } else {
        addMessage('charlie', '(no response)');
      }

    } catch (err) {
      typingEl.remove();
      addMessage('charlie', `Oops, something went wrong: ${err}`);
      console.error('Chat error:', err);
    } finally {
      isSending = false;
      if (!messageText) input.focus();
    }
  }

  // Ribbon Controls
  function clearChat() {
    container.innerHTML = '';
    addMessage('charlie', 'Chat cleared! How can I help you today?');
  }

  function exportChat() {
    const messages = Array.from(container.querySelectorAll('.message')).map(msg => {
      const role = msg.classList.contains('user') ? 'User' : 'Charlie';
      const content = msg.querySelector('.bubble').textContent;
      const time = msg.querySelector('.meta').textContent;
      return `[${time}] ${role}: ${content}`;
    }).join('\n\n');

    const blob = new Blob([messages], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `charlie-chat-${new Date().toISOString().split('T')[0]}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  }

  function toggleVoice() {
    voiceEnabled = !voiceEnabled;
    const toggleBtn = el('#toggle-voice');

    if (voiceEnabled) {
      document.body.classList.add('voice-enabled');
      toggleBtn.textContent = '🎤 Voice Enabled';
      toggleBtn.style.background = 'rgba(0,224,255,0.2)';
      initializeSpeechRecognition();
    } else {
      document.body.classList.remove('voice-enabled');
      toggleBtn.textContent = '🎤 Enable Voice';
      toggleBtn.style.background = '';
      stopListening();
    }
  }

  function initializeSpeechRecognition() {
    if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
      alert('Speech recognition not supported in this browser');
      return;
    }

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = 'en-US';

    recognition.onstart = () => {
      isListening = true;
      el('#start-listening').disabled = true;
      el('#stop-listening').disabled = false;
      el('#start-listening').classList.add('voice-active');
    };

    recognition.onend = () => {
      isListening = false;
      el('#start-listening').disabled = false;
      el('#stop-listening').disabled = true;
      el('#start-listening').classList.remove('voice-active');
    };

    recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript;
      if (transcript.trim()) {
        sendMessage(transcript);
      }
    };

    recognition.onerror = (event) => {
      console.error('Speech recognition error:', event.error);
      addMessage('charlie', `Voice recognition error: ${event.error}`);
    };
  }

  function startListening() {
    if (recognition && !isListening) {
      recognition.start();
    }
  }

  function stopListening() {
    if (recognition && isListening) {
      recognition.stop();
    }
  }

  function changeModel() {
    const select = el('#model-select');
    currentModel = select.value;
    addMessage('charlie', `Switched to model: ${currentModel}`);
  }

  function openSettings() {
    // Placeholder for settings modal
    alert('Settings panel coming soon!');
  }

  // Ribbon button listeners
  el('#clear-chat')?.addEventListener('click', clearChat);
  el('#export-chat')?.addEventListener('click', exportChat);
  el('#toggle-voice')?.addEventListener('click', toggleVoice);
  el('#start-listening')?.addEventListener('click', startListening);
  el('#stop-listening')?.addEventListener('click', stopListening);
  const modelSelectEl = el('#model-select');
  if (modelSelectEl) modelSelectEl.addEventListener('change', changeModel);
  const settingsBtnEl = el('#settings-btn');
  if (settingsBtnEl) settingsBtnEl.addEventListener('click', openSettings);

  // Send button and Enter key listeners
  sendBtn?.addEventListener('click', () => sendMessage());
  input?.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  });

  // MCP button listeners
  el('#mcp-tools-btn').addEventListener('click', showMcpTools);
  el('#mcp-search-btn').addEventListener('click', () => {
    const query = prompt('What would you like to search for?');
    if (query && query.trim()) {
      performMcpSearch(query.trim());
    }
  });

  // MCP Tool Management
  let availableMcpTools = {};

  async function loadMcpTools() {
    try {
      const response = await fetch('/api/mcp/tools');
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      const data = await response.json();
      availableMcpTools = data.tools;

      console.log('Loaded MCP tools:', availableMcpTools);
      return availableMcpTools;
    } catch (error) {
      console.error('Error loading MCP tools:', error);
      return {};
    }
  }

  async function showMcpTools() {
    const tools = await loadMcpTools();
    let toolList = 'Available MCP Tools:\n\n';

    // Fallback: if no tools are returned, guide the user
    if (!tools || Object.keys(tools).length === 0) {
      toolList += 'No MCP tools are currently loaded.\n\n';
      toolList += '- Try refreshing the page (Ctrl+F5).\n';
      toolList += '- Make sure the web server has restarted.\n';
      toolList += '- Visit /api/mcp/config to verify servers and tools.\n';
      addMessage('charlie', renderRichText(toolList), true);
      return;
    }

    for (const [server, serverTools] of Object.entries(tools)) {
      toolList += `🔧 **${server.toUpperCase()}**\n`;
      serverTools.forEach(tool => {
        toolList += `  • ${tool.name}: ${tool.description}\n`;
      });
      toolList += '\n';
    }

    addMessage('charlie', renderRichText(toolList), true);
  }

  async function performMcpSearch(query) {
    try {
      const response = await fetch('/api/mcp/search', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: query, use_tools: true })
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const data = await response.json();

      let resultsText = `🔍 **MCP Search Results for "${data.query}"**\n\n`;
      resultsText += `**Tools Used:** ${data.tools_used.join(', ')}\n\n`;

      for (const [tool, result] of Object.entries(data.results)) {
        resultsText += `**${tool.toUpperCase()}:**\n`;

        if (tool === 'filesystem' && result.items) {
          resultsText += `Found ${result.items.length} items in ${result.path}\n`;
          result.items.slice(0, 10).forEach(item => {
            const icon = item.type === 'directory' ? '📁' : '📄';
            resultsText += `${icon} ${item.name}\n`;
          });
          if (result.items.length > 10) {
            resultsText += `... and ${result.items.length - 10} more items\n`;
          }
        } else if (tool === 'deepwiki' && result.results) {
          result.results.forEach(r => {
            resultsText += `📖 ${r.title}\n${r.content}\n\n`;
          });
        } else if (tool === 'n8n' && result.workflows) {
          resultsText += `Found ${result.workflows.length} workflows:\n`;
          result.workflows.forEach(wf => {
            resultsText += `• ${wf.name} (ID: ${wf.id})\n`;
          });
        } else {
          resultsText += `${JSON.stringify(result, null, 2)}\n`;
        }

        resultsText += '\n';
      }

      addMessage('charlie', renderRichText(resultsText), true);

    } catch (error) {
      console.error('MCP search error:', error);
      addMessage('charlie', `MCP search error: ${error.message}`);
    }
  }

  // Initialize file browser
  loadFileList();

  // Warm welcome with rich text demo
  setTimeout(() => {
    const welcomeMessage = `Hello! I'm Charlie 🤖

**I now support rich text formatting:**

\`\`\`python
def hello_world():
    print("Hello from Charlie!")
\`\`\`

| Feature | Status |
|---------|--------|
| Code blocks | ✅ |
| Tables | ✅ |
| Voice | 🎤 |
| File Browser | 📁 |
| MCP Tools | 🔧 |

**Try the file browser on the left!** Click on files to read their contents.

**Use MCP Tools:** Click "🔧 Tools" to see available tools, or "🔍 Search" for intelligent searches across multiple data sources.

How can I help you today?`;
  addMessage('charlie', renderRichText(welcomeMessage), true);
  input.focus();
}, 1000);
})();
