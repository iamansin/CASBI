from typing_extensions import Annotated, List, TypedDict
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    message : Annotated[List[str],add_messages]
    tool : Annotated[List[str],add_messages]
    
    

    