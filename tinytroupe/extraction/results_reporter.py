import os
import json
from typing import Union, List, Dict, Any
from rich.console import Console
from rich.markdown import Markdown

from tinytroupe.extraction import logger
from tinytroupe.agent import TinyPerson
from tinytroupe.environment import TinyWorld
from tinytroupe.utils import LLMChat
from tinytroupe import default


class ResultsReporter:
    
    def __init__(self, 
                 default_reporting_task: str = "Summarize the key findings, insights, and outcomes from the simulation data.",
                 verbose: bool = False):
        """
        Initializes the ResultsReporter.
        
        Args:
            default_reporting_task (str): The default task to ask agents when generating reports.
            verbose (bool): Whether to print debug messages.
        """
        self.default_reporting_task = default_reporting_task
        self.verbose = verbose
        self.console = Console()
        
        # Cache for generated reports
        self.last_report = None
    
    def report_from_agents(self,
                          agents: Union[TinyPerson, TinyWorld, List[TinyPerson]],
                          reporting_task: str = None,
                          report_title: str = "Simulation Report",
                          include_agent_summaries: bool = True,
                          consolidate_responses: bool = True,
                          requirements: str = "Present the findings in a clear, structured manner.") -> str:
        """
        Option 1: Generate a report by asking agents about specific reporting tasks.
        
        Args:
            agents: Single agent, TinyWorld, or list of agents to interview.
            reporting_task: The specific task to ask agents about.
            report_title: Title for the generated report.
            include_agent_summaries: Whether to include agent mini-bios in the report.
            consolidate_responses: Whether to consolidate all responses into a single report.
            requirements: Formatting or content requirements for the report.
            
        Returns:
            str: The generated Markdown report.
        """
        if reporting_task is None:
            reporting_task = self.default_reporting_task
            
        # Extract agents from input
        agent_list = self._extract_agents(agents)
        
        if self.verbose:
            logger.info(f"Interviewing {len(agent_list)} agents for report generation.")
        
        # Collect responses from agents
        agent_responses = []
        for agent in agent_list:
            response = self._interview_agent(agent, reporting_task)
            agent_responses.append({
                "agent": agent,
                "response": response
            })
        
        # Generate the report
        report = self._format_agent_interview_report(
            agent_responses, 
            report_title, 
            reporting_task,
            include_agent_summaries,
            consolidate_responses,
            requirements
        )
        
        self.last_report = report
        return report
    
    def report_from_interactions(self,
                                agents: Union[TinyPerson, TinyWorld, List[TinyPerson]],
                                report_title: str = "Interaction Analysis Report",
                                include_agent_summaries: bool = True,
                                first_n: int = None,
                                last_n: int = None,
                                max_content_length: int = None,
                                requirements: str = "Present the findings in a clear, structured manner.") -> str:
        """
        Option 2: Generate a report by analyzing agents' historical interactions.
        
        Args:
            agents: Single agent, TinyWorld, or list of agents to analyze.
            report_title: Title for the generated report.
            include_agent_summaries: Whether to include agent mini-bios.
            first_n: Number of first interactions to include.
            last_n: Number of last interactions to include.
            max_content_length: Maximum content length for interactions.
            requirements: Formatting or content requirements for the report.
            
        Returns:
            str: The generated Markdown report.
        """
        # Extract agents from input
        agent_list = self._extract_agents(agents)
        
        if self.verbose:
            logger.info(f"Analyzing interactions from {len(agent_list)} agents.")
        
        # Collect interaction data
        interactions_data = []
        for agent in agent_list:
            interactions = agent.pretty_current_interactions(
                simplified=True,
                first_n=first_n,
                last_n=last_n,
                max_content_length=max_content_length
            )
            interactions_data.append({
                "agent": agent,
                "interactions": interactions
            })
        
        # Generate the report
        report = self._format_interactions_report(
            interactions_data,
            report_title,
            include_agent_summaries,
            requirements
        )
        
        self.last_report = report
        return report
    
    def report_from_data(self,
                        data: Union[str, Dict[str, Any], List[Dict[str, Any]]],
                        report_title: str = "Data Report",
                        requirements: str = "Present the findings in a clear, structured manner.") -> str:
        """
        Option 3: Generate a report from raw text or structured data.
        
        Args:
            data: Raw text, dictionary, or list of dictionaries to format.
            report_title: Title for the generated report.
            requirements: Formatting or content requirements for the report. If None, uses simple formatting.
            
        Returns:
            str: The generated Markdown report.
        """
        if self.verbose:
            logger.info("Generating report from raw data.")
        
        # Generate the report
        report = self._format_data_report(data, report_title, requirements)
        
        self.last_report = report
        return report
    
    def display_report(self, report: str = None):
        """
        Display a report on the console with rich formatting.
        
        Args:
            report: The report to display. If None, uses the last generated report.
        """
        if report is None:
            report = self.last_report
            
        if report is None:
            self.console.print("[red]No report available to display.[/red]")
            return
            
        markdown = Markdown(report)
        self.console.print(markdown)
    
    def save_report(self, 
                   filename: str,
                   report: str = None,
                   verbose: bool = None):
        """
        Save a report to a file.
        
        Args:
            filename: The filename to save the report to.
            report: The report to save. If None, uses the last generated report.
            verbose: Whether to print confirmation message.
        """
        if report is None:
            report = self.last_report
            
        if report is None:
            raise ValueError("No report available to save.")
            
        if verbose is None:
            verbose = self.verbose

        with open(filename, 'w', encoding='utf-8', errors='replace') as f:
            f.write(report)
            
        if verbose:
            logger.info(f"Report saved to {filename}")
    
    def _extract_agents(self, agents) -> List[TinyPerson]:
        """Extract a list of TinyPerson objects from various input types."""
        if isinstance(agents, TinyPerson):
            return [agents]
        elif isinstance(agents, TinyWorld):
            return agents.agents
        elif isinstance(agents, list):
            return agents
        else:
            raise ValueError("Agents must be a TinyPerson, TinyWorld, or list of TinyPerson objects.")
    
    def _interview_agent(self, agent: TinyPerson, reporting_task: str) -> str:
        """Interview a single agent about the reporting task."""
        if self.verbose:
            logger.debug(f"Interviewing agent {agent.name} about: {reporting_task}")
        
        # Following TinyTroupe patterns - directly interact with the agent
        prompt = f"""
        I need you to provide a comprehensive report based on your experiences and observations.
        
        Reporting task: {reporting_task}
        
        Please provide detailed insights, specific examples, and key findings from your perspective.
        Focus on what you've learned, observed, and experienced during the simulation.
        """
        
        # Use listen_and_act pattern to get agent's response
        agent.listen(prompt)
        actions = agent.act(return_actions=True)
        
        # Extract the response from the agent's actions
        response = ""
        for action in actions:
            if action["action"]["type"] == "TALK":
                response += action["action"]["content"] + "\n"
        
        if self.verbose:
            logger.debug(f"Agent {agent.name} response received.")
        
        return response.strip()
    
    def _format_agent_interview_report(self, 
                                     agent_responses: List[Dict],
                                     title: str,
                                     task: str,
                                     include_summaries: bool,
                                     consolidate: bool,
                                     requirements: str) -> str:
        """Format agent interview responses into a Markdown report."""
        # Prepare data for LLM formatting
        agents_data = []
        for resp in agent_responses:
            agent_info = {
                "name": resp["agent"].name,
                "response": resp["response"]
            }
            if include_summaries:
                agent_info["bio"] = resp["agent"].minibio(extended=False)
            agents_data.append(agent_info)
        
        # Generate report using LLM
        return self._generate_report_with_llm(
            title=title,
            report_type="agent_interview",
            data={
                "reporting_task": task,
                "agents_data": agents_data,
                "consolidate": consolidate
            },
            include_summaries=include_summaries,
            requirements=requirements
        )
    
    def _format_interactions_report(self,
                                  interactions_data: List[Dict],
                                  title: str,
                                  include_summaries: bool,
                                  requirements: str) -> str:
        """Format interaction data into a Markdown report."""
        # Prepare data for LLM formatting
        agents_data = []
        for data in interactions_data:
            agent_info = {
                "name": data["agent"].name,
                "interactions": data["interactions"]
            }
            if include_summaries:
                agent_info["bio"] = data["agent"].minibio(extended=False)
            agents_data.append(agent_info)
        
        # Generate report using LLM
        return self._generate_report_with_llm(
            title=title,
            report_type="interactions",
            data={"agents_data": agents_data},
            include_summaries=include_summaries,
            requirements=requirements
        )
    
    def _format_data_report(self,
                          data: Any,
                          title: str,
                          requirements: str) -> str:
        """Format raw data into a Markdown report."""
        return self._generate_report_with_llm(
            title=title,
            report_type="custom_data",
            data=data,
            requirements=requirements
        )

    
    def _generate_report_with_llm(self,
                                title: str,
                                report_type: str,
                                data: Any,
                                include_summaries: bool = False,
                                requirements: str = None) -> str:
        """Generate a report using LLM based on the report type and data."""
        
        # Base system prompt
        system_prompt = "You are a professional report writer who creates clear, well-structured Markdown reports."
        
        # Type-specific prompts and instructions
        if report_type == "agent_interview":
            system_prompt += " You specialize in synthesizing interview responses from multiple agents."
            user_prompt = f"""
            ## Task
            Create a comprehensive report based on agent interviews such that it fulfills the 
            specified requirements below.
            
            ## Report Title
            {title}
            
            ## Report Details
            - **Reporting Task:** {data['reporting_task']}
            - **Number of Agents Interviewed:** {len(data['agents_data'])}
            - **Generated on:** {self._get_timestamp()}
            
            ## Agent Responses
            {json.dumps(data['agents_data'], indent=2)}
            
            ## Instructions
            - Start with the title as a level-1 header
            - Write a direct, clear report, but do not simplify or summarize the information
            - Make sure all important details are included. This is not a summary, but a detailed report, so you never remove information, you just make it more readable
            - Do not include the original data or agent responses, but only the resulting report information
            - For each agent, include their bio if provided
            - Use proper Markdown formatting throughout
            - Follow the requirements given next, which can also override any of these rules
            
            ## Requirements
            {requirements}
            """
            
        elif report_type == "interactions":
            system_prompt += " You specialize in analyzing and presenting agent interaction histories."
            user_prompt = f"""
            ## Task
            Create a report analyzing agent interactions from a simulation such that it fulfills the 
            specified requirements below.
            
            ## Report Title
            {title}
            
            ## Report Details
            - **Number of Agents Analyzed:** {len(data['agents_data'])}
            - **Generated on:** {self._get_timestamp()}
            
            ## Agent Interaction Data
            {json.dumps(data['agents_data'], indent=2)}
            
            ## Instructions
            - Start with the title as a level-1 header
            - Write a direct, clear report, but do not simplify or summarize the information
            - Make sure all important details are included. This is not a summary, but a detailed report, so you never remove information, you just make it more readable
            - Do not include agents' interaction history, but only the resulting report information
            - For each agent, include their bio if provided
            - Use proper Markdown formatting throughout
            - Follow the requirements given next, which can also override any of these rules
            
            ## Requirements
            {requirements}
            """
            
        elif report_type == "custom_data":
            # Handle arbitrary data without assuming any structure
            if isinstance(data, str):
                data_representation = data
            else:
                # For any other type, convert to JSON for a clean representation
                data_representation = json.dumps(data, indent=2)
                
            user_prompt = f"""
            ## Task
            Create a well-structured Markdown report based on the provided data such that it fulfills the 
            specified requirements below.
            
            ## Report Title
            {title}
            
            ## Generated on
            {self._get_timestamp()}
            
            ## Data to Format
            {data_representation}
            
            ## Instructions
            - Start with the title as a level-1 header
            - Write a direct, clear report, but do not simplify or summarize the information
            - Make sure all important details are included. This is not a summary, but a detailed report, so you never remove information, you just make it more readable
            - Use proper Markdown formatting throughout
            - Follow the requirements given next, which can also override any of these rules
            
            ## Requirements
            {requirements if requirements else "Use your best judgment to create a clear, informative report that presents the data in an organized and readable manner."}
            """
        
        else:
            raise ValueError(f"Unknown report type: {report_type}")
        
        # Generate the report
        report_chat = LLMChat(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            output_type=str,
            enable_json_output_format=False,
            model=default["model"],
            temperature=0.3
        )
        
        return report_chat()
    
    
    def _get_timestamp(self) -> str:
        """Get current timestamp for report headers."""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
