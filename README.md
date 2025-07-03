# Repo Explorer - GitHub MCP Server with Q&A Agent
Build an intelligent question-answering system that can understand and query GitHub repositories using Model Context Protocol (MCP) servers and a Streamlit interface.

## Requirements

### Part 1: GitHub Repository Selection & Analysis
   - Select any public GitHub repository (preferably medium-sized, 100+ files)
   - Examples: Popular open-source projects, documentation repos, or educational codebases
   - Document your choice and reasoning

### Part 2: MCP Server Development
1. **Create MCP Servers** (Choose at least 3 of the following)
   - [x] **File Content Server**: Retrieve and read file contents
   - [x] **Repository Structure Server**: Get directory trees and file listings
   - [ ] **Commit History Server**: Access commit messages and changes
   - [ ] **Issue/PR Server**: Query issues and pull requests
   - [x] **Code Search Server**: Search for specific code patterns or functions
   - [ ] **Documentation Server**: Extract and process README files and docs

2. **MCP Server Specifications**
   - [ ] Each server must implement proper MCP protocol
   - [ ] Include error handling and rate limiting
   - [ ] Support filtering and pagination where applicable
   - [ ] Provide clear tool descriptions for the AI agent

### Part 3: Streamlit Application
1. **Build Q&A Interface**
   - [ ] Clean, intuitive chat-like interface
   - [ ] Display conversation history
   - [ ] Show which MCP tools were used for each response
   - [ ] Include repository information and stats

2. **AI Agent Integration**
   - [ ] Use an LLM (OpenAI, Anthropic, or open-source model)
   - [ ] Implement tool-calling capabilities
   - [ ] Design effective prompts for repository understanding
   - [ ] Handle multi-step reasoning and tool chaining

### Part 4: Advanced Features (Choose 2+)
- [ ] **Code Analysis**: Analyze code quality, complexity, or patterns
- [ ] **Visual Repository Map**: Generate interactive visualizations
- [ ] **Smart Summarization**: Create repository summaries and overviews
- [ ] **Change Detection**: Track and explain recent changes
- [ ] **Dependency Analysis**: Map project dependencies and relationships
- [ ] **Documentation Generation**: Auto-generate missing documentation


## Deliverables
1. **Source Code**
   - [ ] MCP server implementations
   - [ ] Streamlit application code
   - [ ] Configuration files and documentation


## Sample Questions
- "What is this repository about and what does it do?"
- "Show me the main entry points of this application"
- "What are the recent changes in the last 10 commits?"
- "Find all functions related to authentication"
- "What dependencies does this project use?"
- "Are there any open issues related to performance?"
- "Explain how the database connection is implemented"
- "What's the testing strategy used in this project?"
