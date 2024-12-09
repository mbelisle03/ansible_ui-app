# consumers.py

import json
from channels.generic.websocket import AsyncWebsocketConsumer

class JobConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.job_id = self.scope['url_route']['kwargs']['job_id']
        self.room_group_name = f'job_{self.job_id}'

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def send_job_output(self, event):
        output = event['output']
        await self.send(text_data=json.dumps({
            'output': output
        }))