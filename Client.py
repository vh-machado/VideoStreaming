import socket
import threading
import os
import time
from tkinter import *
from tkinter import messagebox
from PIL import Image, ImageTk
from RtpPacket import RtpPacket

CACHE_FILE_NAME = "cache-"
CACHE_FILE_EXT = ".jpg"

DARK_BG = "#2b2b2b"  # Cor de fundo escura
DARK_BG_LIGHTER = "#424242"
DARK_FG = "#ffffff"  # Cor do texto (branco)
BUTTON_BG = "#D0782C"  # Cor de fundo dos botões
BUTTON_ACTIVE_BG = "#505050"  # Cor quando o botão é clicado

class Client:
    INIT = 0
    READY = 1
    PLAYING = 2
    state = INIT

    SETUP = 0
    PLAY = 1
    PAUSE = 2
    TEARDOWN = 3
    DESCRIBE = 4

    def __init__(self, master, serveraddr, serverport, rtpport, filename):
        self.master = master
        self.master.protocol("WM_DELETE_WINDOW", self.handler)
        self.master.configure(bg=DARK_BG)
        self.master.grid_columnconfigure(0, weight=1)
        self.serverAddr = serveraddr
        self.serverPort = int(serverport)
        self.rtpPort = int(rtpport)
        self.fileName = filename

        self.player_frame = None
        self.initiate_variables()


    def initiate_variables(self):
        self.createSetupWidgets()
        self.rtspSeq = 0
        self.sessionId = 0
        self.requestSent = -1
        self.teardownAcked = 0
        self.frameNbr = 0
        self.connectToServer()
        self.is_playing = False

    def toggle_play_pause(self):
        self.is_playing = not self.is_playing
        if self.is_playing:
            self.play_pause_button.config(image=self.pause_icon_photo)
            self.playMovie()
        else:
            self.play_pause_button.config(image=self.play_icon_photo)
            self.pauseMovie()

    def createControlWidgets(self):
        self.player_frame = Frame(self.master, bg=DARK_BG)
        self.player_frame.grid(row=1, column=0, sticky=W+N+E+S)

        self.label = Label(
            self.player_frame,
            bg=DARK_BG,
            fg=DARK_FG,
        )
        self.label.grid(row=0, column=0)

        self.button_frame = Frame(self.player_frame, bg=DARK_BG)
        self.button_frame.place(x=252, y=354)
        self.button_frame.lift()
        self.master.grid_columnconfigure(0, weight=1)

        back_icon = Image.open('./assets/back_icon.png')
        back_icon = back_icon.resize((32, 32), Image.Resampling.LANCZOS)
        back_icon_photo = ImageTk.PhotoImage(back_icon)

        self.teardown = Button(
            self.button_frame,
            image=back_icon_photo,
            command=self.goBack,
            bd=0,
            relief="flat",
            bg=DARK_BG,
            activebackground=DARK_BG,
            highlightthickness=0
        )
        self.teardown.grid(row=1, column=0, padx=2, pady=2)
        self.teardown.image = back_icon_photo

        play_icon = Image.open('./assets/play_icon.png')
        play_icon = play_icon.resize((32, 32), Image.Resampling.LANCZOS)
        self.play_icon_photo = ImageTk.PhotoImage(play_icon)

        pause_icon = Image.open('./assets/pause_icon.png')
        pause_icon = pause_icon.resize((32, 32), Image.Resampling.LANCZOS)
        self.pause_icon_photo = ImageTk.PhotoImage(pause_icon)

        self.play_pause_button = Button(
            self.button_frame,
            image=self.play_icon_photo,
            command=self.toggle_play_pause,
            bd=0,
            relief="flat",
            bg=DARK_BG,
            activebackground=DARK_BG,
            highlightthickness=0
        )
        self.play_pause_button.grid(row=1, column=1, padx=2, pady=2)
        self.play_pause_button.play_image = self.play_icon_photo
        self.play_pause_button.pause_image = self.pause_icon_photo

        info_icon = Image.open('./assets/info_icon.png')
        info_icon = info_icon.resize((32, 32), Image.Resampling.LANCZOS)
        info_icon_photo = ImageTk.PhotoImage(info_icon)

        self.describe = Button(
            self.button_frame,
            image=info_icon_photo,
            command=self.describeMovie,
            bd=0,
            relief="flat",
            bg=DARK_BG,
            activebackground=DARK_BG,
            highlightthickness=0
        )
        self.describe.grid(row=1, column=2, padx=2, pady=2)
        self.describe.image = info_icon_photo

    def createSetupWidgets(self):
        self.setup_frame = Frame(self.master, bg=DARK_BG_LIGHTER)
        self.setup_frame.place(relx=0.5, rely=0.5, anchor="center")

        setup_content = Frame(self.setup_frame, bg=DARK_BG_LIGHTER)
        setup_content.grid(row=1, column=1, pady=5, padx=10, sticky=W+N)

        setup_icon = Image.open('./assets/play_icon.png')
        setup_icon = setup_icon.resize((32, 32), Image.Resampling.LANCZOS)
        setup_icon_photo = ImageTk.PhotoImage(setup_icon)
        setup_icon_label = Label(setup_content, image=setup_icon_photo, bg=DARK_BG_LIGHTER)
        setup_icon_label.grid(row=0, column=0, pady=5, sticky=W)
        setup_icon_label.image = setup_icon_photo

        setup_text = Label(setup_content, text=self.fileName, bg=DARK_BG_LIGHTER, fg=DARK_FG, width=12, anchor='w', justify=LEFT)
        setup_text.grid(row=0, column=1, pady=5, sticky=W)

        self.setup = Button(
            setup_content,
            width=20,
            text="Assistir",
            command=self.setupMovie,
            bg=BUTTON_BG,
            fg=DARK_FG,
            activebackground=BUTTON_ACTIVE_BG,
            activeforeground=DARK_FG,
            relief="flat"
        )
        self.setup.grid(row=1, column=0, columnspan=2, pady=10)

    def describeMovie(self):
      if self.state == self.READY:
          self.sendRtspRequest(self.DESCRIBE)

    def setupMovie(self):
        if self.state == self.INIT:
            self.sendRtspRequest(self.SETUP)
            self.setup_frame.place_forget()

            time.sleep(1)
            self.is_playing = not self.is_playing
            self.playMovie()

            time.sleep(1)
            self.createControlWidgets()
            self.play_pause_button.config(image=self.pause_icon_photo)

    def goBack(self):
        self.teardownMovie()
        self.player_frame.grid_forget()
        self.player_frame = None
        time.sleep(1)
        self.initiate_variables()

    def teardownMovie(self):
        self.sendRtspRequest(self.TEARDOWN)

        try:
            os.remove(CACHE_FILE_NAME + str(self.sessionId) + CACHE_FILE_EXT)
        except:
            print('Cache file not found')

    def pauseMovie(self):
        if self.state == self.PLAYING:
            self.sendRtspRequest(self.PAUSE)

    def playMovie(self):
        if self.state == self.READY:
            threading.Thread(target=self.listenRtp).start()
            self.playEvent = threading.Event()
            self.playEvent.clear()
            self.sendRtspRequest(self.PLAY)

    def listenRtp(self):
        while True:
            try:
                data = self.rtpSocket.recv(20480)
                if data:
                    rtpPacket = RtpPacket()
                    rtpPacket.decode(data)
                    currFrameNbr = rtpPacket.seqNum()
                    if currFrameNbr > self.frameNbr:
                        self.frameNbr = currFrameNbr
                        self.updateMovie(self.writeFrame(rtpPacket.getPayload()))
            except:
                if self.playEvent.isSet():
                    break
                if self.teardownAcked == 1:
                    self.rtpSocket.close()
                    break

    def writeFrame(self, data):
        cachename = CACHE_FILE_NAME + str(self.sessionId) + CACHE_FILE_EXT
        with open(cachename, "wb") as file:
            file.write(data)
        return cachename

    def updateMovie(self, imageFile):
        photo = Image.open(imageFile)
        photo = photo.resize((600, 400), Image.Resampling.LANCZOS)
        photo = ImageTk.PhotoImage(photo)
        self.label.configure(image=photo)
        self.label.image = photo

    def connectToServer(self):
        self.rtspSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.rtspSocket.connect((self.serverAddr, self.serverPort))
        except:
            messagebox.showwarning('Connection Failed', f"Connection to '{self.serverAddr}' failed.")

    def sendRtspRequest(self, requestCode):
        self.rtspSeq += 1
        if requestCode == self.SETUP:
            threading.Thread(target=self.recvRtspReply).start()
            request = f"SETUP {self.fileName} RTSP/1.0\nCSeq: {self.rtspSeq}\nTransport: RTP/UDP; client_port= {self.rtpPort}"
            self.requestSent = self.SETUP
        elif requestCode == self.PLAY:
            request = f"PLAY {self.fileName} RTSP/1.0\nCSeq: {self.rtspSeq}\nSession: {self.sessionId}"
            self.requestSent = self.PLAY
        elif requestCode == self.PAUSE:
            request = f"PAUSE {self.fileName} RTSP/1.0\nCSeq: {self.rtspSeq}\nSession: {self.sessionId}"
            self.requestSent = self.PAUSE
        elif requestCode == self.TEARDOWN:
            request = f"TEARDOWN {self.fileName} RTSP/1.0\nCSeq: {self.rtspSeq}\nSession: {self.sessionId}"
            self.requestSent = self.TEARDOWN
        elif requestCode == self.DESCRIBE:
            request = f"DESCRIBE {self.fileName} RTSP/1.0\nCSeq: {self.rtspSeq}\nSession: {self.sessionId}"
            self.requestSent = 'DESCRIBE'
        else:
            return
        self.rtspSocket.send(request.encode())

    def recvRtspReply(self):
        while True:
            reply = self.rtspSocket.recv(1024).decode()
            if reply:
                self.parseRtspReply(reply)
            if self.requestSent == self.TEARDOWN:
                self.rtspSocket.close()
                break

    def parseRtspReply(self, data):
        lines = data.split('\n')
        seqNum = int(lines[1].split(' ')[1])
        if seqNum == self.rtspSeq:
            session = int(lines[2].split(' ')[1])
            if self.sessionId == 0:
                self.sessionId = session
            if self.sessionId == session:
                status_code = int(lines[0].split(' ')[1])
                if status_code == 200:
                    if self.requestSent == self.SETUP:
                        self.state = self.READY
                        self.openRtpPort()
                    elif self.requestSent == self.PLAY:
                        self.state = self.PLAYING
                    elif self.requestSent == self.PAUSE:
                        self.state = self.READY
                        self.playEvent.set()
                    elif self.requestSent == self.TEARDOWN:
                        self.state = self.INIT
                        self.teardownAcked = 1
                    elif self.requestSent == 'DESCRIBE':
                        self.processDescribeReply(lines)
    
    def processDescribeReply(self, lines):
        print("Descrição do fluxo de mídia recebida:")
        for line in lines:
            if line.startswith('m='):
                print(line)
    
        # Exibir mensagem para o usuário
        messagebox.showinfo("Descrição do fluxo", "\n".join(lines))

    def openRtpPort(self):
        self.rtpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.rtpSocket.settimeout(0.5)
        try:
            self.rtpSocket.bind(("", self.rtpPort))
        except:
            messagebox.showwarning('Unable to Bind', f"Unable to bind PORT={self.rtpPort}")

    def handler(self):
        if self.player_frame:
            self.pauseMovie()
        if messagebox.askokcancel("Sair", "Tem certeza que deseja sair?"):
            if self.player_frame:
                self.teardownMovie()
            self.master.destroy()
        else:
            if self.player_frame:
                self.playMovie()
