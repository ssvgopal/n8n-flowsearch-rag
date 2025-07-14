# n8n RAG Workflows

A collection of n8n workflows for Retrieval-Augmented Generation (RAG) applications, enabling you to build powerful AI-powered automation with ease.

## 🚀 Features

- **Pre-built RAG Workflows**: Ready-to-use n8n workflows for various RAG applications
- **Multi-Platform Integration**: Connect with various data sources and AI models
- **Customizable**: Easily adapt the workflows to your specific needs
- **Open Source**: MIT Licensed - use, modify, and distribute freely

## 📋 Prerequisites

- [n8n](https://n8n.io/) installed and running
- Access to AI models (e.g., OpenAI, Anthropic, etc.)
- Required API keys for the services you plan to use

## 🛠️ Setup

1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/n8n-rag-workflows.git
   cd n8n-rag-workflows
   ```

2. Set up your environment variables:
   - Copy `.env.example` to `.env`
   - Update the values with your API keys and configuration

3. Import the workflows into your n8n instance

## 🔧 Configuration

Create a `.env` file in the root directory with your API keys:

```env
# OpenAI
OPENAI_API_KEY=your_openai_api_key

# Other API keys as needed
# ANTHROPIC_API_KEY=your_anthropic_api_key
# PINECONE_API_KEY=your_pinecone_api_key
```

## 📦 Included Workflows

- **Document Q&A**: Chat with your documents using AI
- **Knowledge Base Assistant**: Create a searchable knowledge base
- **Content Summarizer**: Generate summaries from various content sources
- **And more...**

## 🤝 Contributing

Contributions are welcome! Please read our [Contributing Guidelines](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [n8n](https://n8n.io/) for the amazing workflow automation platform
- All contributors who help improve this project
