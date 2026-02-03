"""
上海宇羲伏天智能科技有限公司出品

文件级注释：基于 LangGraph 的智能体服务层
内部逻辑：定义 Agent 状态、工具集、ReAct 节点及图流转逻辑
设计模式：依赖注入 + 注册表模式
设计原则：开闭原则、依赖倒置原则
"""

from typing import Annotated, List, TypedDict, Dict, Any
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool, BaseTool
from langgraph.graph import StateGraph, END
from langchain_community.vectorstores import Chroma
from app.core.config import settings
from app.services.ingest_service import IngestService
from app.utils.llm_factory import LLMFactory
from app.services.agent.tool_registry import ToolRegistry


# 类级：定义智能体状态
class AgentState(TypedDict):
    """
    类级注释：智能体运行状态
    属性：
        messages: 消息历史列表
        sources: 检索到的来源列表 (doc_id)
    """
    messages: Annotated[List[BaseMessage], lambda x, y: x + y]
    sources: Annotated[List[int], lambda x, y: list(set(x + y))]


class AgentService:
    """
    类级注释：智能体服务类，构建并运行 LangGraph 工作流
    """

    # 类级注释：工具映射字典，用于通过名称查找工具
    _tools_map: Dict[str, BaseTool] = {}
    # 类级注释：存储上次检索的文档 ID
    _last_retrieved_ids: List[int] = []

    def __init__(self):
        """
        函数级注释：初始化智能体服务
        内部逻辑：使用工厂模式创建LLM实例，从工具注册表获取工具
        设计模式：依赖注入 + 注册表模式
        """
        # 内部变量：初始化模型
        # 内部逻辑：使用工厂模式创建LLM实例，支持多提供商切换
        self.llm = LLMFactory.create_llm(streaming=False)

        # 内部变量：初始化向量库用于检索工具
        embeddings = IngestService.get_embeddings()
        self.vector_db = Chroma(
            persist_directory=settings.CHROMA_DB_PATH,
            embedding_function=embeddings,
            collection_name=settings.CHROMA_COLLECTION_NAME
        )

        # 内部逻辑：设置工具注册表的依赖（向量库）
        ToolRegistry.set_dependencies(vector_db=self.vector_db)

        # 内部逻辑：从工具注册表获取工具（解耦）
        self.tools = ToolRegistry.get_all()

        # 内部逻辑：构建工具名称映射字典
        AgentService._tools_map = ToolRegistry.get_tools_map()

        # 内部逻辑：将工具绑定到模型（部分模型支持，若不支持则需通过 Prompt 引导）
        self.model_with_tools = self.llm.bind_tools(self.tools)

    def _call_model(self, state: AgentState) -> Dict[str, Any]:
        """
        函数级注释：调用大模型生成响应或工具调用指令
        参数：state - 智能体当前状态
        返回值：包含新消息的字典
        """
        messages = state['messages']
        response = self.model_with_tools.invoke(messages)
        return {"messages": [response]}

    def _execute_tools(self, state: AgentState) -> Dict[str, Any]:
        """
        函数级注释：执行模型提出的工具调用请求
        参数：state - 智能体当前状态
        返回值：包含工具执行结果消息和来源的字典
        """
        last_message = state['messages'][-1]
        tool_messages = []

        # 内部逻辑：处理多工具并行调用
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            for tool_call in last_message.tool_calls:
                # 内部逻辑：通过名称查找工具并执行
                tool_name = tool_call.get("name", "")
                tool_args = tool_call.get("args", {})
                tool = AgentService._tools_map.get(tool_name)

                if tool:
                    try:
                        # 内部逻辑：执行工具调用
                        result = tool.invoke(tool_args)
                        tool_messages.append(
                            ToolMessage(
                                content=str(result),
                                tool_call_id=tool_call.get("id", "")
                            )
                        )
                    except Exception as e:
                        # 内部逻辑：处理工具执行异常
                        tool_messages.append(
                            ToolMessage(
                                content=f"工具执行出错: {str(e)}",
                                tool_call_id=tool_call.get("id", "")
                            )
                        )
                else:
                    # 内部逻辑：处理工具未找到的情况
                    tool_messages.append(
                        ToolMessage(
                            content=f"未找到工具: {tool_name}",
                            tool_call_id=tool_call.get("id", "")
                        )
                    )

        return {
            "messages": tool_messages,
            "sources": AgentService._last_retrieved_ids.copy()
        }

    def _should_continue(self, state: AgentState) -> str:
        """
        函数级注释：根据最后一条消息判断是否继续执行工具或结束
        参数：state - 智能体当前状态
        返回值：下一个节点名称 ("action" 或 END)
        """
        last_message = state['messages'][-1]
        # 内部逻辑：如果模型输出了 tool_calls，则进入 action 节点
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "action"
        return END

    def create_graph(self):
        """
        函数级注释：构建 LangGraph 状态机图
        返回值：编译后的图对象
        """
        workflow = StateGraph(AgentState)

        # 内部逻辑：添加节点
        workflow.add_node("agent", self._call_model)
        workflow.add_node("action", self._execute_tools)

        # 内部逻辑：设置入口
        workflow.set_entry_point("agent")

        # 内部逻辑：添加条件边
        workflow.add_conditional_edges(
            "agent",
            self._should_continue,
            {
                "action": "action",
                END: END
            }
        )

        # 内部逻辑：动作执行完后回到 agent 思考
        workflow.add_edge("action", "agent")

        return workflow.compile()

    async def run(self, query: str, history: List[BaseMessage] = None) -> Dict[str, Any]:
        """
        函数级注释：运行智能体解决问题
        参数：
            query: 用户输入问题
            history: 对话历史
        返回值：包含回答和来源 ID 的字典
        """
        app = self.create_graph()

        # 内部逻辑：准备初始消息列表
        messages = [SystemMessage(content="你是一个专业的知识库助手，你可以通过检索本地知识库来回答问题。请始终用中文回答。")]
        if history:
            messages.extend(history)
        messages.append(HumanMessage(content=query))

        # 内部逻辑：重置检索 ID
        AgentService._last_retrieved_ids = []

        # 内部逻辑：异步运行获取最终状态
        inputs = {"messages": messages, "sources": []}
        final_state = await app.ainvoke(inputs)

        return {
            "answer": final_state["messages"][-1].content,
            "sources": final_state.get("sources", [])
        }
