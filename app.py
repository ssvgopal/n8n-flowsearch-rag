#!/usr/bin/env python3
"""
n8n RAG Service for Railway Deployment
Simplified version for reliable deployment
"""

from flask import Flask, request, jsonify
import json
from pathlib import Path
import re
from typing import List, Dict, Any, Optional
import logging
import os

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

class SimpleN8nRAGService:
    def __init__(self):
        # Get workflows from environment variable or use default
        self.workflows_dir = os.getenv('WORKFLOWS_DIR', 'workflows/json_files')
        self.workflows = self.load_workflows()
        logger.info(f"Loaded {len(self.workflows)} workflows")
    
    def load_workflows(self) -> List[Dict[str, Any]]:
        """Load workflows from directory, handling complex JSON structures"""
        workflows = []
        workflows_path = Path(self.workflows_dir)
        
        logger.info(f"Workflows directory: {workflows_path}")
        
        if not workflows_path.exists():
            logger.warning(f"Workflows directory {workflows_path} does not exist")
            # Return some sample workflows for testing
            return self.get_sample_workflows()
        
        try:
            for file_path in workflows_path.glob("*.json"):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        
                        # Handle different JSON structures
                        if isinstance(data, dict):
                            # Single workflow object
                            workflow = data
                            workflow['_filename'] = file_path.name
                            workflows.append(workflow)
                        elif isinstance(data, list):
                            # Complex list structure - try to extract workflow data
                            workflow_data = self.extract_workflow_from_complex_structure(data, file_path.name)
                            if workflow_data:
                                workflows.append(workflow_data)
                        else:
                            logger.warning(f"Skipping {file_path}: unexpected JSON structure (type={type(data)})")
                            
                except Exception as e:
                    logger.error(f"Error loading {file_path}: {e}")
        except Exception as e:
            logger.error(f"Error accessing workflows directory: {e}")
            return self.get_sample_workflows()
        
        logger.info(f"Loaded {len(workflows)} workflows from {workflows_path}")
        
        # Validate all workflows are proper dicts
        valid_workflows = []
        for i, workflow in enumerate(workflows):
            if not isinstance(workflow, dict):
                logger.warning(f"Skipping workflow {i}: not a dict (type={type(workflow)})")
                continue
            valid_workflows.append(workflow)
        
        logger.info(f"Valid workflows: {len(valid_workflows)} out of {len(workflows)}")
        return valid_workflows
    
    def extract_workflow_from_complex_structure(self, data: List, filename: str) -> Optional[Dict[str, Any]]:
        """Extract workflow data from complex serialized structures"""
        try:
            # Look for workflow-like objects in the data
            workflow_candidates = []
            
            def find_workflow_objects(obj, path=""):
                if isinstance(obj, dict):
                    # Check if this looks like a workflow object - must have at least name or title
                    if ('name' in obj or 'title' in obj) and isinstance(obj, dict):
                        # Ensure it's a proper workflow object with expected structure
                        if 'name' in obj or 'title' in obj or 'nodes' in obj or 'connections' in obj:
                            workflow_candidates.append((obj, path))
                    # Recursively search nested objects
                    for key, value in obj.items():
                        find_workflow_objects(value, f"{path}.{key}" if path else key)
                elif isinstance(obj, list):
                    # Recursively search list items
                    for i, item in enumerate(obj):
                        find_workflow_objects(item, f"{path}[{i}]" if path else f"[{i}]")
            
            find_workflow_objects(data)
            
            if workflow_candidates:
                # Use the first workflow-like object found
                workflow, path = workflow_candidates[0]
                
                # Ensure the workflow has the required fields
                if not isinstance(workflow, dict):
                    logger.warning(f"Extracted object from {filename} is not a dict: {type(workflow)}")
                    return None
                
                # Add required fields if missing
                if 'name' not in workflow and 'title' in workflow:
                    workflow['name'] = workflow['title']
                elif 'name' not in workflow and 'title' not in workflow:
                    workflow['name'] = f"Workflow from {filename}"
                
                if 'nodes' not in workflow:
                    workflow['nodes'] = []
                
                if 'connections' not in workflow:
                    workflow['connections'] = {}
                
                workflow['_filename'] = filename
                workflow['_extracted_from'] = path
                logger.info(f"Extracted workflow from {filename} at path: {path}")
                return workflow
            else:
                logger.warning(f"No workflow data found in {filename}")
                return None
                
        except Exception as e:
            logger.error(f"Error extracting workflow from {filename}: {e}")
            return None
    
    def get_sample_workflows(self) -> List[Dict[str, Any]]:
        """Return sample workflows for testing when no files are found"""
        return [
            {
                "name": "Sample Slack Notification Workflow",
                "description": "Sends Slack notifications when new emails arrive",
                "nodes": [
                    {"name": "Gmail Trigger", "type": "n8n-nodes-base.gmailTrigger"},
                    {"name": "Slack", "type": "n8n-nodes-base.slack"}
                ],
                "connections": {
                    "Gmail Trigger": [{"main": [{"node": "Slack"}]}]
                },
                "_filename": "sample_slack_workflow.json"
            },
            {
                "name": "Sample Data Sync Workflow", 
                "description": "Syncs data between Google Sheets and Airtable",
                "nodes": [
                    {"name": "Google Sheets", "type": "n8n-nodes-base.googleSheets"},
                    {"name": "Airtable", "type": "n8n-nodes-base.airtable"}
                ],
                "connections": {
                    "Google Sheets": [{"main": [{"node": "Airtable"}]}]
                },
                "_filename": "sample_sync_workflow.json"
            }
        ]
    
    def search_workflows(self, query: str, n_results: int = 3) -> List[Dict[str, Any]]:
        """Simple keyword search"""
        results = []
        query_lower = query.lower()
        
        for workflow in self.workflows:
            try:
                # Ensure workflow is a dict
                if not isinstance(workflow, dict):
                    logger.warning(f"Skipping non-dict workflow: {type(workflow)}")
                    continue
                
                score = 0
                workflow_text = f"{workflow.get('name', '')} {workflow.get('description', '')}".lower()
                
                # Simple scoring
                if query_lower in workflow_text:
                    score += 10
                
                # Check node types
                nodes = workflow.get('nodes', [])
                if isinstance(nodes, list):
                    for node in nodes:
                        if isinstance(node, dict):
                            node_type = node.get('type', '').lower()
                            if query_lower in node_type:
                                score += 5
                
                if score > 0:
                    results.append({
                        'workflow': workflow,
                        'score': score
                    })
            except Exception as e:
                logger.error(f"Error processing workflow in search: {e}")
                continue
        
        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:n_results]
    
    def format_examples(self, query: str) -> str:
        """Format search results as examples"""
        results = self.search_workflows(query)
        
        if not results:
            return "No specific examples found. Using general n8n workflow patterns."
        
        examples_text = "## Relevant Workflow Examples:\n\n"
        
        for i, result in enumerate(results, 1):
            workflow = result['workflow']
            examples_text += f"### Example {i}: {workflow.get('name', 'Unnamed')}\n"
            examples_text += f"**Relevance Score:** {result['score']}\n\n"
            
            # Show nodes
            nodes = workflow.get('nodes', [])
            if nodes:
                examples_text += "**Nodes:**\n"
                for j, node in enumerate(nodes[:5], 1):
                    node_name = node.get('name', 'Unnamed')
                    node_type = node.get('type', 'unknown')
                    examples_text += f"{j}. {node_name} ({node_type})\n"
            
            examples_text += "\n"
        
        return examples_text

# Initialize the RAG service
rag_service = SimpleN8nRAGService()

@app.route('/')
def root():
    """Root endpoint"""
    return jsonify({
        'service': 'n8n RAG Service',
        'version': '1.0.0',
        'status': 'running',
        'workflows_loaded': len(rag_service.workflows),
        'endpoints': {
            'health': '/health',
            'enhance_prompt': '/enhance-prompt',
            'search': '/search'
        }
    })

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'workflows_loaded': len(rag_service.workflows),
        'message': f"RAG service loaded {len(rag_service.workflows)} workflows"
    })

@app.route('/enhance-prompt', methods=['POST'])
def enhance_prompt():
    """Main endpoint for enhancing prompts"""
    try:
        data = request.json
        if not data or 'query' not in data:
            return jsonify({'error': 'Missing query parameter'}), 400
        
        user_query = data['query']
        logger.info(f"Processing query: {user_query}")
        
        # Get relevant examples
        examples = rag_service.format_examples(user_query)
        
        # Enhanced system prompt
        enhanced_prompt = f"""# Overview
You are an expert AI automation developer specializing in building workflows for n8n. Your job is to translate a human's natural language request into a fully functional n8n workflow JSON.

## Available Knowledge Base
You have access to a comprehensive database of {len(rag_service.workflows)} real n8n workflows, including official n8n team workflows and community examples.

{examples}

## Instructions
1. Analyze the user request and the provided examples
2. Identify relevant patterns and node combinations from the examples
3. Generate a workflow that follows similar patterns but is customized for the user's specific needs
4. Ensure the workflow is complete, functional, and follows n8n best practices

## Output Requirements
Your output should only be the final JSON of the full workflow, starting with {{ and ending with }}.

User Request: {user_query}
"""
        
        return jsonify({
            'enhanced_prompt': enhanced_prompt,
            'examples_found': len(rag_service.search_workflows(user_query)) > 0,
            'workflows_searched': len(rag_service.workflows),
            'query': user_query
        })
        
    except Exception as e:
        logger.error(f"Error processing request: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/search', methods=['POST'])
def search_workflows():
    """Search endpoint"""
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
                    'filename': r['workflow'].get('_filename', 'unknown')
                }
                for r in results
            ]
        })
        
    except Exception as e:
        logger.error(f"Error in search: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    logger.info(f"Starting n8n RAG Service on port {port}")
    logger.info(f"Workflows loaded: {len(rag_service.workflows)}")
    app.run(host='0.0.0.0', port=port, debug=False) 
