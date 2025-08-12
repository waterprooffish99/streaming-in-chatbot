import os
from dotenv import load_dotenv
from typing import cast
import chainlit as cl
from agents import Agent, Runner, AsyncOpenAI, OpenAIChatCompletionsModel
from agents.run import RunConfig

load_dotenv()
gemini_api_key = os.getenv("GEMINI_API_KEY")

#Check if an api key present, if not raise an error...

if not gemini_api_key:
    raise ValueError("GEMINI_API_KEY is not set, please insure it is defined")


@cl.on_chat_start
async def start():
    #Reference : http://ai.google.dev/gemini-api/docs/openai

    external_client = AsyncOpenAI(
        api_key = gemini_api_key,
        base_url = "https://generativelanguage.googleapis.com/v1beta/openai"
    )

    model = OpenAIChatCompletionsModel(
        model = "gemini-2.0-flash",
        openai_client = external_client
    )

    config = RunConfig(
        model = model,
        model_provider = external_client,
        tracing_disabled = True
    )

    cl.user_session.set("chat_history", [])
    cl.user_session.set("config", config)

    agent = Agent(name = "Assistant" , instructions = "You are a helpful Assistant", model = model)

    cl.user_session.set("agent", agent)
    await cl.Message(content = "Welcome to the ChatBot Created By Waterproof Fish, How can I help you today?").send()
    
@cl.on_message
async def main(message: cl.Message):
      
       history = cl.user_session.get("chat_history") or []
       history.append({"role": "user", "content": message.content })

       msg = cl.Message(content = "")
       await msg.send()

       agent : Agent = cast(Agent, cl.user_session.get("agent"))
       config : RunConfig = cast(RunConfig, cl.user_session.get("config"))
     
       try:
            print("\n[CALLING_AGENT_WITH_CONTEXT]\n", history, "\n")
            result = Runner.run_streamed(agent, history, run_config = config)
            async for event in result.stream_events():
                if event.type == "raw_response_event" and hasattr(event.data, "delta"):
                    token = event.data.delta
                    await msg.stream_token(token)
            history.append({"role": "assistant", "content": msg.content})
            cl.user_session.set("chat_history", history)

            print(f"User: {message.content}")
            print(f"Assistant: {msg.content}")
       except Exception as e:
            msg.content = f"Error: {str(e)}"
            await msg.update()
            print(f"Error: {str(e)}")