import threading

from langchain.agents import AgentExecutor, create_react_agent

_executor_cache = {}
_executor_cache_lock = threading.Lock()
_MAX_EXECUTOR_CACHE_SIZE = 16


def get_cached_executor(
    cache_key: str,
    llm,
    tools,
    react_prompt,
    max_iterations: int = 4,
    max_execution_time: int = 30,
):
    with _executor_cache_lock:
        if cache_key in _executor_cache:
            print(f"[AGENT_CACHE] hit key={cache_key}")
            return _executor_cache[cache_key]

        print(f"[AGENT_CACHE] miss key={cache_key}")
        agent = create_react_agent(llm=llm, tools=tools, prompt=react_prompt)
        executor = AgentExecutor(
            agent=agent,
            tools=tools,
            verbose=False,
            handle_parsing_errors=True,
            max_iterations=max_iterations,
            max_execution_time=max_execution_time,
        )
        _executor_cache[cache_key] = executor

        if len(_executor_cache) > _MAX_EXECUTOR_CACHE_SIZE:
            first_key = next(iter(_executor_cache.keys()))
            if first_key != cache_key:
                _executor_cache.pop(first_key, None)

        return executor
