# Agentic Repo Explorer

Intelligent question-answering system that can understand and query GitHub repositories using Model Context Protocol (MCP) servers and a Streamlit interface with ReAct and Planner agent implemented with Langgraph.

## Installation instructions
To run the app locally, first install `uv` from the [Official Website](https://docs.astral.sh/uv/getting-started/installation/)

### To install and run the virtual environment
```
$ uv venv

$ source .venv/bin/activate
```

### To install all the dependencies from pyproject.toml
```
$ uv pip install 
```

### To run the Streamlit app
```
$ streamlit run main.py
```

## Progress:

### Part 1: GitHub Repository Selection & Analysis
   - I've selected `psf/requests` repo since it is one of the most used packages and relatively large.

### Part 2: MCP Server Development
1. **Create MCP Servers** (Choose at least 3 of the following)
   - [x] **File Content Server**: Retrieve and read file contents
   - [x] **Repository Structure Server**: Get directory trees and file listings
   - [x] **Commit History Server**: Access commit messages and changes
   - [x] **Issue/PR Server**: Query issues and pull requests
   - [x] **Code Search Server**: Search for specific code patterns or functions
   - [x] **Documentation Server**: Extract and process README files and docs

2. **MCP Server Specifications**
   - [x] Each server must implement proper MCP protocol
   - [ ] Include error handling and rate limiting - Partially.
   - [ ] Support filtering and pagination where applicable - Partially.
   - [x] Provide clear tool descriptions for the AI agent

### Part 3: Streamlit Application
1. **Build Q&A Interface**
   - [x] Clean, intuitive chat-like interface
   - [x] Display conversation history
   - [x] Show which MCP tools were used for each response
   - [ ] Include repository information and stats

2. **AI Agent Integration**
   - [x] Use an LLM (OpenAI, Anthropic, or open-source model)
   - [x] Implement tool-calling capabilities
   - [x] Design effective prompts for repository understanding
   - [x] Handle multi-step reasoning and tool chaining

### Part 4: Advanced Features (Choose 2+)
- [x] **Code Analysis**: Analyze code quality, complexity, or patterns
- [ ] **Visual Repository Map**: Generate interactive visualizations
- [x] **Smart Summarization**: Create repository summaries and overviews
- [x] **Change Detection**: Track and explain recent changes
- [ ] **Dependency Analysis**: Map project dependencies and relationships - Partially.
- [x] **Documentation Generation**: Auto-generate missing documentation


## Deliverables
1. **Source Code**
   - [x] MCP server implementations
   - [x] Streamlit application code
   - [x] Configuration files and documentation


## Sample Questions
- "What is this repository about and what does it do?" - DONE
- "Show me the main entry points of this application" - DONE
- "What are the recent changes in the last 10 commits?" - DONE
- "Find all functions related to authentication" - DONE
- "What dependencies does this project use?" - DONE
- "Are there any open issues related to performance?" - DONE
- "Explain how the database connection is implemented"
- "What's the testing strategy used in this project?" - DONE
