import lightning as L
from src.components.explorer import SchemaDiscovery
from src.components.executor import SQLAgent
from src.components.trainer import SelfImprover

class NL2SQLApp(L.LightningFlow):
    def __init__(self):
        super().__init__()
        # Component 1: The Explorer (Schema & Semantics)
        self.discovery = SchemaDiscovery()
        
        # Component 2: The Executor (SLM Agent)
        self.agent = SQLAgent()
        
        # Component 3: The Trainer (Self-Improvement)
        self.improver = SelfImprover()

    def run(self):
        # 1. Discovery Phase (Runs once or on demand)
        # For now, we assume a db_url is passed or configured
        if not self.discovery.has_run:
            self.discovery.run()
        
        # 2. Agent Loop (Always running/ready to serve)
        self.agent.run()
        
        # 3. Improver Loop (Runs periodically or completely parallel)
        self.improver.run()

app = L.LightningApp(NL2SQLApp())
