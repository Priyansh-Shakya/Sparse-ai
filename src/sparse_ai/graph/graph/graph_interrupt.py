


"""
Whenever Graph Needs to pause - Long Pause , Approval etc
LLM will generate a small Interrupt model:
Intterup: ### Need to decide if this will be a Interupt class TYPE or Final Answer before Graph stops.
{
'reason': "Reason of intterup (e.g. Human Approval)",
'data': {
        'title': '...',
        'task' : '...',
        ...
    } , #Approval data
'verdit' : "LLM's question asking if the above data is correct or needs changes however the user want ..."
}
"""


class GraphInterrupt(Exception):
    def __init__(self, reason , data , verdict):
        self.reason = reason
        self.data = data
        self.verdict = verdict
        super().__init__(reason)
    def __repr__(self):
        return f"{self.__class__.__name__}(Reason={self.reason}, Data={self.data}, Verdict={self.verdict}"