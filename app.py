#!/usr/bin/env python3
"""
n8n RAG Service for Cloud Deployment
Optimized for Railway, Render, or other cloud platforms
"""

from flask import Flask, request, jsonify
import json
from pathlib import Path
import re
from typing import List, Dict, Any
import logging
import os

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

class CloudN8nRAGService:
    def __init__(self):
        # Get workflows from environment variable or use default
        self.workflows_dir = os.getenv('WORKFLOWS_DIR', 'workflows/json_files')
        self.workflows = self.load_workflows()
        logger.info(f"Loaded {len(self.workflows)} workflows")
    
    def load_workflows(self) -> List[Dict[str, Any]]:
        """Load workflows from local directory"""
        workflows = []
        workflows_path = Path(self.workflows_dir)
        
        if not workflows_path.exists():
            logger.warning(f"Workflows directory {workflows_path} does not exist")
            return workflows
        
        for file_path in workflows_path.glob("*.json"):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    workflow = json.load(f)
                    workflow['_filename'] = file_path.name
                    workflows.append(workflow)
            except Exception as e:
                logger.error(f"Error loading {file_path}: {e}")
        
        return workflows
    
    def extract_workflow_text(self, workflow: Dict[str, Any]) -> str:
        """Extract searchable text from a workflow"""
        text_parts = []
        
        # Workflow metadata
        name = workflow.get('name', 'Unnamed Workflow')
        description = workflow.get('description', '')
        tags = workflow.get('tags', [])
        
        text_parts.append(f"Workflow: {name}")
        if description:
            text_parts.append(f"Description: {description}")
        if tags:
            text_parts.append(f"Tags: {', '.join(tags)}")
        
        # Node information
        nodes = workflow.get('nodes', [])
        for node in nodes:
            node_name = node.get('name', 'Unnamed')
            node_type = node.get('type', 'unknown')
            text_parts.append(f"Node: {node_name} ({node_type})")
            
            # Extract key parameters
            params = node.get('parameters', {})
            if params:
                for key, value in params.items():
                    if isinstance(value, (str, int, float, bool)):
                        text_parts.append(f"  {key}: {value}")
        
        return " ".join(text_parts)
    
    def search_workflows(self, query: str, n_results: int = 3) -> List[Dict[str, Any]]:
        """Search workflows using keyword matching"""
        results = []
        query_lower = query.lower()
        query_words = set(re.findall(r'\w+', query_lower))
        
        for workflow in self.workflows:
            score = 0
            workflow_text = self.extract_workflow_text(workflow).lower()
            
            # Exact phrase matches (highest priority)
            if query_lower in workflow_text:
                score += 20
            
            # Word matches
            workflow_words = set(re.findall(r'\w+', workflow_text))
            word_matches = len(query_words.intersection(workflow_words))
            score += word_matches * 3
            
            # Node type matches
            nodes = workflow.get('nodes', [])
            for node in nodes:
                node_type = node.get('type', '').lower()
                if any(word in node_type for word in query_words):
                    score += 5
                
                # Check node name
                node_name = node.get('name', '').lower()
                if any(word in node_name for word in query_words):
                    score += 3
            
            # Workflow name/description matches
            workflow_name = workflow.get('name', '').lower()
            workflow_desc = workflow.get('description', '').lower()
            
            if any(word in workflow_name for word in query_words):
                score += 8
            if any(word in workflow_desc for word in query_words):
                score += 6
            
            if score > 0:
                results.append({
                    'workflow': workflow,
                    'score': score,
                    'text': self.extract_workflow_text(workflow)
                })
        
        # Sort by score and return top results
        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:n_results]
    
    def format_examples(self, query: str) -> str:
        """Format search results as examples for the LLM prompt"""
        results = self.search_workflows(query)
        
        if not results:
            return "No specific examples found for this query. Using general n8n workflow patterns."
        
        examples_text = "## Relevant Workflow Examples:\n\n"
        
        for i, result in enumerate(results, 1):
            workflow = result['workflow']
            examples_text += f"### Example {i}: {workflow.get('name', 'Unnamed')}\n"
            examples_text += f"**Relevance Score:** {result['score']}\n"
            examples_text += f"**Source:** {workflow.get('_filename', 'unknown')}\n\n"
            
            # Extract key nodes and their types
            nodes = workflow.get('nodes', [])
            examples_text += "**Key Nodes:**\n"
            for j, node in enumerate(nodes[:6], 1):  # Show first 6 nodes
                node_name = node.get('name', 'Unnamed')
                node_type = node.get('type', 'unknown')
                examples_text += f"{j}. {node_name} ({node_type})\n"
            
            # Show connection pattern
            connections = workflow.get('connections', {})
            if connections:
                examples_text += "\n**Connection Pattern:**\n"
                for from_node, to_nodes in list(connections.items())[:3]:  # Show first 3 connections
                    for connection in to_nodes:
                        for to_node in connection:
                            examples_text += f"  {from_node} → {to_node['node']}\n"
            
            examples_text += "\n"
        
        return examples_text
    
    def get_workflow_statistics(self) -> Dict[str, Any]:
        """Get statistics about the workflow collection"""
        if not self.workflows:
            return {"total_workflows": 0}
        
        # Count node types
        node_types = {}
        trigger_types = {}
        app_integrations = set()
        
        for workflow in self.workflows:
            nodes = workflow.get('nodes', [])
            for node in nodes:
                node_type = node.get('type', 'unknown')
                node_types[node_type] = node_types.get(node_type, 0) + 1
                
                # Extract app name from node type
                if '.' in node_type:
                    app_name = node_type.split('.')[0]
                    app_integrations.add(app_name)
                
                # Identify triggers
                if 'trigger' in node_type.lower():
                    trigger_types[node_type] = trigger_types.get(node_type, 0) + 1
        
        return {
            "total_workflows": len(self.workflows),
            "unique_node_types": len(node_types),
            "unique_apps": len(app_integrations),
            "unique_triggers": len(trigger_types),
            "top_node_types": sorted(node_types.items(), key=lambda x: x[1], reverse=True)[:10],
            "top_triggers": sorted(trigger_types.items(), key=lambda x: x[1], reverse=True)[:5],
            "apps": list(app_integrations)
        }

# Initialize the RAG service
rag_service = CloudN8nRAGService()

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for cloud platforms"""
    stats = rag_service.get_workflow_statistics()
    return jsonify({
        'status': 'healthy',
        'workflows_loaded': stats['total_workflows'],
        'message': f"RAG service loaded {stats['total_workflows']} workflows",
        'environment': os.getenv('RAILWAY_ENVIRONMENT', 'development')
    })

@app.route('/enhance-prompt', methods=['POST'])
def enhance_prompt():
    """Main endpoint for enhancing prompts with workflow examples"""
    try:
        data = request.json
        if not data or 'query' not in data:
            return jsonify({'error': 'Missing query parameter'}), 400
        
        user_query = data['query']
        logger.info(f"Processing query: {user_query}")
        
        # Get relevant examples
        examples = rag_service.format_examples(user_query)
        
        # Get workflow statistics
        stats = rag_service.get_workflow_statistics()
        
        # Enhanced system prompt
        enhanced_prompt = f"""# Overview
You are an expert AI automation developer specializing in building workflows for n8n. Your job is to translate a human's natural language request into a fully functional n8n workflow JSON.

## Available Knowledge Base
You have access to a comprehensive database of {stats['total_workflows']} real n8n workflows, including official n8n team workflows and community examples. The knowledge base includes:
- {stats['unique_apps']} different app integrations
- {stats['unique_node_types']} different node types
- {stats['unique_triggers']} different trigger types

{examples}

## Instructions
1. Analyze the user request and the provided examples
2. Identify relevant patterns and node combinations from the examples
3. Generate a workflow that follows similar patterns but is customized for the user's specific needs
4. Ensure the workflow is complete, functional, and follows n8n best practices
5. Use the node types and connection patterns shown in the examples as a reference

## Output Requirements
Your output should only be the final JSON of the full workflow, starting with {{ and ending with }}.

User Request: {user_query}
"""
        
        return jsonify({
            'enhanced_prompt': enhanced_prompt,
            'examples_found': len(rag_service.search_workflows(user_query)) > 0,
            'workflows_searched': stats['total_workflows'],
            'query': user_query
        })
        
    except Exception as e:
        logger.error(f"Error processing request: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/search', methods=['POST'])
def search_workflows():
    """Direct search endpoint for testing"""
    try:
        data = request.json
        query = data.get('query', '')
        n_results = data.get('n_results', 3)
        
        results = rag_service.search_workflows(query, n_results)
        
        return jsonify({
            'query': query,
            'results': [
                {
                    'name': r['workflow'].get('name', 'Unnamed'),
                    'score': r['score'],
                    'filename': r['workflow'].get('_filename', 'unknown'),
                    'text': r['text'][:500] + "..." if len(r['text']) > 500 else r['text']
                }
                for r in results
            ]
        })
        
    except Exception as e:
        logger.error(f"Error in search: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/stats', methods=['GET'])
def get_statistics():
    """Get workflow collection statistics"""
    stats = rag_service.get_workflow_statistics()
    return jsonify(stats)

@app.route('/', methods=['GET'])
def root():
    """Root endpoint with service information"""
    return jsonify({
        'service': 'n8n RAG Service',
        'version': '1.0.0',
        'endpoints': {
            'health': '/health',
            'enhance_prompt': '/enhance-prompt',
            'search': '/search',
            'stats': '/stats'
        },
        'documentation': 'See n8n_agent_integration_guide.md for usage instructions'
    })

if __name__ == '__main__':
    # Get port from environment (for cloud platforms)
    port = int(os.getenv('PORT', 5000))
    
    logger.info("Starting n8n RAG Service (Cloud Version)...")
    logger.info(f"Port: {port}")
    logger.info(f"Workflows loaded: {len(rag_service.workflows)}")
    
    # Print initial statistics
    stats = rag_service.get_workflow_statistics()
    logger.info(f"Total workflows: {stats['total_workflows']}")
    logger.info(f"Available apps: {', '.join(stats['apps'][:10])}...")
    
    app.run(host='0.0.0.0', port=port, debug=False) 
