import re
from langchain_core.prompts import PromptTemplate
from typing import Any, Dict, List, Optional, Tuple
from langchain_core.language_models import BaseLanguageModel
from utils.agentmemory import AgentMemory
from utils.track_tokens import token_tracker
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from utils.prompts import agentPromptJson

class Agent:
    id_counter = 0
    def __init__(self, name : str, llm : BaseLanguageModel, 
                 description : str,  memory : AgentMemory, 
                 age : Optional[int] = None,status=""):
        self.name : str = name
        self.llm : BaseLanguageModel = llm
        self.description : str = description
        self.status : str = status
        self.id = self.id_counter
        self.memory : AgentMemory = memory
        self.summary : str = "" # meta_data
        self.age : Optional[int] = age
        # make this some sort of time steps
        self.summary_refresh_seconds : int = 3600 
        self.last_refreshed : datetime = datetime.now()
        self.daily_summaries : List[str] = []
        Agent.id_counter += 1

    def _parse_list(self, text: str) -> List[str]:
        """Parse a newline-separated string into a list of strings."""
        lines = re.split(r"\n", text.strip())
        return [re.sub(r"^\s*\d+\.\s*", "", line).strip() for line in lines]
    
    def chain(self, prompt : PromptTemplate):
        return prompt | self.llm
    

    @token_tracker
    def _get_entity_from_observation(self, observation: str) -> str:
        prompt = PromptTemplate.from_template(agentPromptJson['_get_entity_from_observation'])
        return self.chain(prompt).invoke({"observation":observation})

    @token_tracker
    def _get_entity_action(self, observation: str, entity_name: str) -> str:
        prompt = PromptTemplate.from_template(agentPromptJson['_get_entity_action'])
        return (
            self.chain(prompt).invoke({"entity":entity_name, "observation":observation})
        )
    
    @token_tracker
    def summarize_related_memories(self, observation: str) -> str:
        """Summarize memories that are most relevant to an observation."""
        prompt = PromptTemplate.from_template(agentPromptJson['summarize_related_memories'])
        entity_name = self._get_entity_from_observation(observation)
        entity_action = self._get_entity_action(observation, entity_name)
        relevant_memories = self.memory.fetch_memories(observation=observation)
        q1 = f"What is the relationship between {self.name} and {entity_name}"
        q2 = f"{entity_name} is {entity_action}"
        return self.chain(prompt=prompt).invoke({"q1":q1, "queries":[q1, q2], "relevant_memories" : relevant_memories})
    
    def _clean_response(self, text: str) -> str:
        return re.sub(f"^{self.name} ", "", text.strip()).strip()
    
    @token_tracker
    def _compute_agent_summary(self) -> str:
        """"""
        prompt = PromptTemplate.from_template(agentPromptJson['_compute_agent_summary'])
        # The agent seeks to think about their core characteristics.
        relevant_memories = self.memory.fetch_memories(observation=self.name)
        return (
            self.chain(prompt)
            .invoke({
                "name":self.name, 
                "queries":[f"{self.name}'s core characteristics"],
                "relevant_memories":relevant_memories
            })
        )
    
    def get_summary(
        self, force_refresh: bool = False, now: Optional[datetime] = None
    ) -> str:
        """Return a descriptive summary of the agent."""
        current_time = datetime.now() if now is None else now
        since_refresh = (current_time - self.last_refreshed).seconds
        if (
            not self.summary
            or since_refresh >= self.summary_refresh_seconds
            or force_refresh
        ):
            self.summary = self._compute_agent_summary()
            self.last_refreshed = current_time
        age = self.age if self.age is not None else "N/A"
        return (
            f"Name: {self.name} (age: {age})"
            + f"\nInnate traits: {self.description}"
            + f"\n{self.summary}"
        )
    
    @token_tracker
    def _generate_reaction(
        self, observation: str, suffix: str, now: Optional[datetime] = None, last_k : Optional[int] = 15
    ) -> str:
        """React to a given observation or dialogue act."""
        prompt = PromptTemplate.from_template(agentPromptJson['_generate_reaction'] + suffix)

        with ThreadPoolExecutor() as executor:
            agent_summary_thread = executor.submit(self.get_summary, now=now)
            relevant_memories_thread = executor.submit(self.summarize_related_memories, observation)

            agent_summary_description = agent_summary_thread.result()
            relevant_memories_str = relevant_memories_thread.result()

        # agent_summary_description = self.get_summary(now=now)
        # self.memory.add_memory(memory_content=agent_summary_description)
        # relevant_memories_str = self.summarize_related_memories(observation)

        most_recent_memories = self.memory.memory_retriever.memory_stream[-last_k:]
        most_recent_memories_str = "\n".join(
            [self.memory._format_memory_detail(o) for o in most_recent_memories]
        )

        current_time_str = (
            datetime.now().strftime("%B %d, %Y, %I:%M %p")
            if now is None
            else now.strftime("%B %d, %Y, %I:%M %p")
        )
        kwargs: Dict[str, Any] = {
            "agent_summary_description":agent_summary_description,
            "current_time":current_time_str,
            "relevant_memories":relevant_memories_str,
            "agent_name":self.name,
            "observation":observation,
            "agent_status":self.status,
            "most_recent_memories":most_recent_memories_str
        }
        # consumed_tokens = self.llm.get_num_tokens(
        #     prompt.format(most_recent_memories="", **kwargs)
        # )
        # kwargs[self.memory.most_recent_memories_token_key] = consumed_tokens
        return self.chain(prompt=prompt).invoke(kwargs)
    
    # look into save_context later
    def generate_reaction(
        self, observation: str, now: Optional[datetime] = None,
        call_to_action_template = (agentPromptJson['generate_reaction']),
        villager = "None"
    ) -> Tuple[bool, str]:
        """React to a given observation."""
     
        full_result = self._generate_reaction(
            observation, call_to_action_template, now=now
        )
        result = full_result.strip().split("\n")[0]

        self.memory.save_context(
            {},
            {
                self.memory.add_memory_key: f"{self.name} observed "
                f"{observation} and reacted by {result}",
                self.memory.now_key: now,
            },
            str(self.name)
        )
        if "ELIMINATE:" in result:
            print("*"*50)
            print("KILL")
            print("*"*50)
            reaction = self._clean_response(result.split("ELIMINATE:")[-1])
            return False, f"{self.name} : {villager} has been eliminated"
        elif "REACT:" in result:
            reaction = self._clean_response(result.split("REACT:")[-1])
            return False, f"{self.name} : {reaction}"
        elif "SAY:" in result:
            said_value = self._clean_response(result.split(f"SAY: {self.name}:")[-1])
            return True, f"{self.name} : {said_value}"
        else:
            return False, result
        
    def generate_dialogue_response(
        self, observation: str, now: Optional[datetime] = None,
        call_to_action_template = (agentPromptJson['generate_dialogue_response']),
        villager="None"
    ) -> Tuple[bool, str]:
        """React to a given observation."""
        full_result = self._generate_reaction(
            observation, call_to_action_template, now=now
        )
        
        result = full_result.strip().split("\n")[0]
        if "ELIMINATE:" in result:

            kill = self._clean_response(result.split("ELIMINATE:")[-1])
            self.memory.save_context(
                {},
                {
                    self.memory.add_memory_key: f"{self.name} observed "
                    f"{observation} and eliminated {villager}",
                    self.memory.now_key: now,
                },
                str(self.name)
            )
            return False, f"{self.name} : {villager} has been eliminated"
        elif "GOODBYE:" in result:
            farewell = self._clean_response(result.split("GOODBYE:")[-1])
            self.memory.save_context(
                {},
                {
                    self.memory.add_memory_key: f"{self.name} observed "
                    f"{observation} and said {farewell}",
                    self.memory.now_key: now,
                },
                str(self.name)
            )
            return False, f"{self.name} : {farewell}"
        elif "SAY:" in result:
            response_text = self._clean_response(result.split(":")[-1])
            self.memory.save_context(
                {},
                {
                    self.memory.add_memory_key: f"{self.name} observed "
                    f"{observation} and said {response_text}",
                    self.memory.now_key: now,
                },
                str(self.name)
            )
            return True, f"{self.name} : {response_text}"
        else:
            return False, result
        
    def get_full_header(
        self, force_refresh: bool = False, now: Optional[datetime] = None
    ) -> str:
        """Return a full header of the agent's status, summary, and current time."""

        now = datetime.now() if now is None else now
        summary = self.get_summary(force_refresh=force_refresh, now=now)
        current_time_str = now.strftime("%B %d, %Y, %I:%M %p")
        return (
            f"{summary}\nIt is {current_time_str}.\n{self.name}'s status: {self.status}"
        )

    def reset(self):
        self.id_counter = 0
