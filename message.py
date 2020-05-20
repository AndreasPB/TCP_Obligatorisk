# Kikset forsøg på at refacturere dublikeret kode om til OOP


HEADER = 8
FORMAT = 'utf-8'



# class Message:

    # def send(self, msg, client):
    #     # Define a new variable and encode it to bytes with given FORMAT constant
    #     message = msg.encode(FORMAT)
    #     msg_length = len(message)
    #     send_length = str(msg_length).encode(FORMAT)
    #     send_length += b' ' * (HEADER - len(send_length))
    #     client.send(send_length)
    #     client.send(message)