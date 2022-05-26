#Channels + Websockets - to establish a two way communication and open connection between our client and server.
#Websockets on the client side to initiate a connection
#Channels on the server side to receive and sed request back to the client
#Consumers - Channels Version of Django Views
#Use build-in Javascript websocket API on the client side to initiate handshake and create an open connection between our client and server
#Routing Configuration - channel's routing configuration is an asgi application that is similar to django configuration - tells channels what code to run when an http request is receieved by a channel server
#Channel Layers - Allow us to create an interaction between multiple comsumer instances of an application for real time communication (optional)
#Channel Layer: Groups and Channels
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async #storing things in database inside the asynchronous view
from .models import Message, Room
from django.contrib.auth.models import User

class ChatConsumer(AsyncWebsocketConsumer): #to connect and disconect to the chat server
    async def connect(self):
        self.room_name=self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = 'chat_%s' % self.room_name

        #to join to group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept() #authenticated and connected to the server

    #to leave group
    async def disconnect(self):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    #receive message from websocket
    async def receive(self, text_data): #receive the message and broadcast it to the whole channel
        data = json.loads(text_data)
        message = data['message']
        username = data['username']
        room = data['room']
        image_caption = data['image_caption'] #new
        message_type = data['message_type'] #new

        await self.save_message(username, room, message)
        
        #send to the group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message' : message,
                'username' : username,
                'room' : room,
                'message_type' : message_type, #new
                'image_caption' : image_caption, #new
            }
        )

    #receive message from group
    async def chat_message(self,event):
        message = event['message']
        username = event['username']
        room = event['room']
        message_type = event['message_type'] #new
        image_caption = event['image_caption'] #new

        #send message to websocket
        await self.send(text_data=json.dumps({
            'message' : message,
            'username': username,
            'room': room,
            'message_type' : message_type, #new
            'image_caption' : image_caption, #new
        })) 

    #makes it possible to store things in database when we use the await self.send
    @sync_to_async
    #synchronous views
    def save_message(self, username, room, message):
        user = User.objects.get(username=username)
        room = Room.objects.get(slug=room) #slug is passed in frontend

        Message.objects.create(user=user, room=room, content=message)