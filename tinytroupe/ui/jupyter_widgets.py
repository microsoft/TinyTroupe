"""
TinyTroupe Jupyter Widgets

This module provides interactive widgets for Jupyter notebooks that enable
seamless interaction with TinyTroupe agents and environments.

Classes:
    AgentChatJupyterWidget: An interactive chat interface for conversing with TinyTroupe agents

Dependencies:
    - ipywidgets: For creating interactive notebook widgets
    - IPython.display: For displaying content in notebooks
    - datetime: For timestamping conversations
    - threading: For non-blocking animations
    - tinytroupe: Core TinyTroupe functionality

Example usage:
    ```python
    from tinytroupe.ui.jupyter_widgets import AgentChatJupyterWidget
    from tinytroupe.factory import TinyPersonFactory
    
    # Create some agents
    factory = TinyPersonFactory.create_factory_from_demography("path/to/demographics.json")
    agents = factory.generate_people(5)
    
    # Create and display the chat interface
    chat_widget = AgentChatJupyterWidget(agents)
    chat_widget.display()
    ```
"""

import ipywidgets as widgets
from IPython.display import display, HTML
import datetime
import threading
import tinytroupe
import time


class AgentChatJupyterWidget:
    """
    An interactive chat widget for conversing with TinyTroupe agents in Jupyter notebooks.
    
    This widget provides a user-friendly interface for chatting with one or more TinyTroupe
    agents. It features an animated loading indicator, message history, and responsive design.
    
    Features:
        - Agent selection dropdown
        - Real-time message input and display
        - Single Enter key press to send messages (fixed double-press issue)
        - Animated loading indicators while agents process messages
        - Message history with timestamps
        - Error handling and user feedback
        - Responsive design with proper styling
        - Throttling to prevent accidental double-sending
        - Communication display control (checkbox to show/hide agent output in notebook)
    
    Attributes:
        agents (dict): Dictionary mapping agent names to agent objects
        conversation_history (list): List of conversation entries
        loading_animation_active (bool): Whether loading animation is currently active
        loading_frames (list): Animation frames for the loading spinner
        current_loading_frame (int): Current frame index for animation
    """
    
    def __init__(self, agents_list):
        """
        Initialize the chat widget with a list of agents.
        
        Args:
            agents_list (list): List of TinyTroupe agent objects to make available for chat
        """
        self.agents = {agent.name: agent for agent in agents_list}
        self.conversation_history = []
        self.loading_animation_active = False
        self.loading_frames = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
        self.current_loading_frame = 0
        self._processing = False  # To prevent multiple simultaneous sends
        self._last_message = ""  # Track last message to detect user input vs programmatic changes
        self.setup_widgets()
    
    def setup_widgets(self):
        """
        Set up the UI widgets and their event handlers.
        
        Creates the agent dropdown, message input, buttons, and conversation display.
        Also wires up event handlers for user interactions.
        """
        # Agent selector
        self.agent_dropdown = widgets.Dropdown(
            options=list(self.agents.keys()),
            description='Chat with:',
            style={'description_width': 'initial'}
        )
        
        # Message input
        self.message_input = widgets.Text(
            placeholder='Type your message and press Enter...',
            layout=widgets.Layout(width='70%'),
            continuous_update=False
        )
        
        # Track the last message to detect actual user input vs programmatic changes
        self._last_message = ""
        
        # Send button
        self.send_button = widgets.Button(
            description='Send',
            button_style='primary',
            layout=widgets.Layout(width='80px')
        )
        
        # Clear button
        self.clear_button = widgets.Button(
            description='Clear',
            button_style='warning',
            layout=widgets.Layout(width='80px')
        )
        
        # Communication display checkbox
        self.communication_display_checkbox = widgets.Checkbox(
            value=False,
            description='Show agent communication in notebook output',
            style={'description_width': 'initial'},
            layout=widgets.Layout(width='auto')
        )
        
        # Conversation display
        self.conversation_display = widgets.HTML(
            value="<div style='border: 1px solid #ccc; padding: 10px; height: 400px; overflow-y: scroll; background-color: #f9f9f9;'><p><em>Start a conversation by selecting an agent and typing a message...</em></p></div>"
        )
        
        # Wire up events
        self.send_button.on_click(self._handle_send_click)
        self.clear_button.on_click(self.clear_conversation)
        
        # Use observe method to detect Enter key presses through value changes
        # This is the modern recommended approach for ipywidgets
        self.message_input.observe(self._handle_input_change, names='value')
        
        # Layout
        input_row = widgets.HBox([
            self.agent_dropdown,
            self.message_input,
            self.send_button,
            self.clear_button
        ])
        
        self.widget = widgets.VBox([
            widgets.HTML("<h3>💬 Agent Chat Interface</h3>"),
            input_row,
            self.communication_display_checkbox,
            self.conversation_display
        ])
    
    def _handle_send_click(self, b):
        """Handle send button clicks."""
        if not self._processing:
            self.send_message()
    
    def _handle_input_change(self, change):
        """
        Handle input changes using the observe method.
        
        This method detects when the user has entered text and committed it
        (typically by pressing Enter). We use the observe pattern to monitor
        value changes rather than the deprecated on_submit method.
        
        Args:
            change (dict): The change event containing 'old' and 'new' values
        """
        new_value = change['new'].strip()
        old_value = change['old'].strip()
        
        # Only process if:
        # 1. We're not already processing a message
        # 2. There's actual text in the new value
        # 3. The value actually changed (user input, not programmatic change)
        # 4. This isn't the programmatic clearing we do after sending
        if (not self._processing and 
            new_value and 
            new_value != old_value and 
            new_value != self._last_message):
            
            self._last_message = new_value
            self.send_message()
    
    def send_message(self):
        """
        Send a message to the selected agent and handle the response.
        
        This method:
        1. Validates input
        2. Displays user message immediately
        3. Shows animated loading indicator
        4. Processes agent response in the background
        5. Updates the conversation display
        """
        print("Sending message...")  # Debug print to track message sending
        # Prevent double-sending with processing flag
        if self._processing:
            return
        
        self._processing = True
        
        agent_name = self.agent_dropdown.value
        message = self.message_input.value.strip()
        
        if not message or not agent_name:
            self._processing = False
            return

        
        agent = self.agents[agent_name]
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        
        # Clear input immediately and add user message to history first
        self.message_input.value = ''
        self._last_message = ""  # Reset tracking variable
        
        # Add user message to history and display immediately
        self.conversation_history.append({
            'timestamp': timestamp,
            'sender': 'You',
            'message': message,
            'type': 'user'
        })
        
        # Update display to show user message immediately
        self.update_conversation_display()
        
        # Add animated loading indicator while processing
        loading_entry = {
            'timestamp': timestamp,
            'sender': agent_name,
            'message': '🤔 Processing...',
            'type': 'loading'
        }
        self.conversation_history.append(loading_entry)
        
        # Start animated loading indicator
        self.start_loading_animation(loading_entry)
        
        # Process agent response in background thread
        def process_response():
            try:
                # Use the proper TinyTroupe interaction method
                # Get the communication display setting from the checkbox
                communication_display = self.communication_display_checkbox.value
                actions = agent.listen_and_act(message, return_actions=True, communication_display=communication_display)
                
                # Extract agent responses from the actions
                agent_responses = []
                
                if actions:
                    for action_item in actions:
                        if isinstance(action_item, dict) and 'action' in action_item:
                            action = action_item['action']
                            action_type = action.get('type', '')
                            action_content = action.get('content', '')
                            
                            # Collect TALK and THINK actions as responses
                            if action_type == 'TALK' and action_content:
                                agent_responses.append(f"🗣️ {action_content}")
                            elif action_type == 'THINK' and action_content:
                                agent_responses.append(f"💭 {action_content}")
                
                # Combine all responses or provide fallback
                if agent_responses:
                    agent_response = '\n\n'.join(agent_responses)
                else:
                    agent_response = f"I heard your message: '{message}', but I don't have much to say about it right now."
                
                # Stop loading animation and remove loading indicator
                self.stop_loading_animation()
                self.conversation_history.pop()  # Remove the loading message
                
                # Add agent response to history
                self.conversation_history.append({
                    'timestamp': datetime.datetime.now().strftime("%H:%M:%S"),
                    'sender': agent_name,
                    'message': agent_response,
                    'type': 'agent'
                })
                
            except Exception as e:
                # Handle errors gracefully
                error_msg = f"Error communicating with agent: {str(e)}"
                if hasattr(e, '__class__'):
                    error_msg += f" (Type: {e.__class__.__name__})"
                
                # Stop loading animation and remove loading indicator
                self.stop_loading_animation()
                self.conversation_history.pop()  # Remove the loading message
                
                self.conversation_history.append({
                    'timestamp': datetime.datetime.now().strftime("%H:%M:%S"),
                    'sender': 'System',
                    'message': error_msg,
                    'type': 'error'
                })
            
            finally:
                # Update display with final result and reset processing flag
                self.update_conversation_display()
                self._processing = False
        
        # Start processing in background thread
        threading.Thread(target=process_response, daemon=True).start()
    
    def clear_conversation(self, b=None):
        """
        Clear the conversation history and reset the display.
        
        Args:
            b: Button object (when called from button click, None when called directly)
        """
        if not self._processing:
            self.conversation_history = []
            self.update_conversation_display()
    
    def update_conversation_display(self):
        """
        Update the HTML display of the conversation history.
        
        This method renders all conversation entries with appropriate styling
        based on their type (user, agent, loading, error).
        """
        if not self.conversation_history:
            html_content = "<div style='border: 1px solid #ccc; padding: 10px; height: 400px; overflow-y: scroll; background-color: #f9f9f9;'><p><em>Start a conversation...</em></p></div>"
        else:
            messages_html = []
            for entry in self.conversation_history:
                if entry['type'] == 'user':
                    messages_html.append(f"""
                    <div style='margin: 5px 0; padding: 8px; background-color: #e3f2fd; border-radius: 10px; text-align: right;'>
                        <strong>You ({entry['timestamp']}):</strong> {entry['message']}
                    </div>
                    """)
                elif entry['type'] == 'agent':
                    messages_html.append(f"""
                    <div style='margin: 5px 0; padding: 8px; background-color: #f1f8e9; border-radius: 10px;'>
                        <strong>{entry['sender']} ({entry['timestamp']}):</strong><br>
                        <div style='white-space: pre-wrap; margin-top: 5px;'>{entry['message']}</div>
                    </div>
                    """)
                elif entry['type'] == 'loading':
                    messages_html.append(f"""
                    <div style='margin: 5px 0; padding: 8px; background-color: #fff3cd; border-radius: 10px;'>
                        <strong>{entry['sender']} ({entry['timestamp']}):</strong> <em>{entry['message']}</em>
                    </div>
                    """)
                else:  # error
                    messages_html.append(f"""
                    <div style='margin: 5px 0; padding: 8px; background-color: #ffebee; border-radius: 10px;'>
                        <strong>{entry['sender']} ({entry['timestamp']}):</strong> <em>{entry['message']}</em>
                    </div>
                    """)
            
            html_content = f"""
            <div style='border: 1px solid #ccc; padding: 10px; height: 400px; overflow-y: scroll; background-color: #f9f9f9;'>
                {''.join(messages_html)}
            </div>
            """
        
        self.conversation_display.value = html_content
    
    def start_loading_animation(self, loading_entry):
        """
        Start the animated loading indicator.
        
        This method creates a smooth spinning animation that updates the loading
        message with different spinner frames at regular intervals.
        
        Args:
            loading_entry (dict): The conversation entry containing the loading message
        """
        self.loading_animation_active = True
        self.current_loading_frame = 0
        
        def animate():
            if self.loading_animation_active:
                # Update the loading message with current animation frame
                spinner = self.loading_frames[self.current_loading_frame % len(self.loading_frames)]
                loading_entry['message'] = f'{spinner} Processing...'
                self.update_conversation_display()
                self.current_loading_frame += 1
                
                # Schedule next frame after 200ms
                threading.Timer(0.2, animate).start()
        
        animate()
    
    def stop_loading_animation(self):
        """
        Stop the loading animation.
        
        This method sets the animation flag to False, causing the animation
        loop to stop at the next iteration.
        """
        self.loading_animation_active = False
    
    def display(self):
        """
        Display the chat widget in the notebook.
        
        This method should be called to render the widget in a Jupyter notebook cell.
        """
        display(self.widget)