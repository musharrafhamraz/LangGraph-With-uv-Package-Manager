from typing import Dict, Any, Optional
from datetime import datetime

from langchain_groq import ChatGroq
from langchain.prompts import ChatPromptTemplate
from langchain.schema import StrOutputParser


class ContentCreator:
    """Class to generate LinkedIn article content using LLM."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the content creator with a Groq API key.
        
        Args:
            api_key: Groq API key. If None, will look for GROQ_API_KEY in environment variables.
        """
        self.api_key = api_key
        self.llm = self._initialize_llm()
    
    def _initialize_llm(self) -> ChatGroq:
        """Initialize the Groq LLM.
        
        Returns:
            ChatGroq: Initialized Groq LLM.
        """
        return ChatGroq(
            model="llama3-70b-8192",  # Using Llama 3 70B model
            temperature=0.7,  # Moderate creativity
            api_key=self.api_key
        )
    
    def generate_article(self, preferences: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a LinkedIn article based on user preferences.
        
        Args:
            preferences: Dictionary containing user preferences for the article.
                        Should include 'topics', 'tone', and optionally 'length'.
            
        Returns:
            Dict[str, Any]: Dictionary containing the generated article title and content.
        """
        # Extract preferences
        topics = preferences.get("topics", [])
        tone = preferences.get("tone", "professional")
        length = preferences.get("length", "medium")
        
        # Convert topics list to a comma-separated string
        topics_str = ", ".join(topics) if isinstance(topics, list) else topics
        
        # Define the prompt template
        prompt_template = ChatPromptTemplate.from_template(
            """You are a professional LinkedIn content creator. Your task is to create a high-quality 
            LinkedIn article on the following topics: {topics}.
            
            The article should have the following characteristics:
            - Tone: {tone}
            - Length: {length} (short: 300-500 words, medium: 500-800 words, long: 800-1200 words)
            - Include a catchy title
            - Include relevant hashtags at the end
            - Be well-structured with clear sections
            - Provide valuable insights or actionable advice
            - Be engaging and professional
            
            Format your response as a JSON object with the following structure:
            {{
                "title": "Your catchy title here",
                "content": "The full article content here, including hashtags at the end"
            }}
            
            Only return the JSON object, nothing else.
            """
        )
        
        # Create the chain
        chain = prompt_template | self.llm | StrOutputParser()
        
        try:
            # Generate the article
            result = chain.invoke({"topics": topics_str, "tone": tone, "length": length})
            
            # Parse the result as JSON
            import json
            article = json.loads(result)
            
            # Add generation timestamp
            article["generated_at"] = datetime.now().isoformat()
            
            return article
        except Exception as e:
            # Return an error message if generation fails
            return {
                "title": "Error Generating Article",
                "content": f"Failed to generate article: {str(e)}",
                "generated_at": datetime.now().isoformat(),
                "error": True
            }