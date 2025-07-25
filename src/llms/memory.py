import sqlite3
import os
import openai

from typing import Dict, Literal, override, Iterable
from colorama import Fore, Style


class Agent(openai.OpenAI):

    def __init__(self, api_key:str , base_url: str, model: str):
        super(Agent, self).__init__(api_key=api_key, base_url=base_url)
        self.model = model
        self.memory: list = [
            {'role': 'system', 'content': 'You are a helpul ai assistant.'}
        ]

    def query(self, prompt: str, stream: bool = True):

        self.memory.append(
            {
                'role': 'user',
                'content': prompt
            }
        )

        response = self.chat.completions.create(
            model=self.model,
            messages=self.memory,
            stream=stream
        )

        if not stream:
            content = response.choices[0].message.content # type: ignore
            print(f'{Fore.CYAN}{content}{Style.RESET_ALL}')
            return content

        msg = ''
        for chunk in response:
            content = getattr(chunk.choices[0].delta, 'content', None) # type: ignore
            if content:
                msg += content
                print(f'{Fore.CYAN}{content}', end='', flush=True)
        
        print(f'{Style.RESET_ALL}')

        self.memory.append(
            {
                'role': 'assistant',
                'content': msg
            }
        )

        return msg