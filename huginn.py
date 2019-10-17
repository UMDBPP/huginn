import logging
import os
import tkinter
import tkinter.filedialog
import tkinter.messagebox
from datetime import datetime

from huginn import radio, tracks, BALLOON_CALLSIGNS


class HuginnGUI:
    def __init__(self):
        self.main_window = tkinter.Tk()
        self.main_window.title('huginn main')

        self.connections = {}

        self.running = False
        self.packet_tracks = {}

        self.frames = {}
        self.elements = {}
        self.last_row = 0

        self.frames['top'] = tkinter.Frame(self.main_window)
        self.frames['top'].pack()

        self.frames['separator'] = tkinter.Frame(height=2, bd=1, relief=tkinter.SUNKEN)
        self.frames['separator'].pack(fill=tkinter.X, padx=5, pady=5)

        self.frames['bottom'] = tkinter.Frame(self.main_window)
        self.frames['bottom'].pack()

        self.__add_entry_box(self.frames['top'], 'port')

        self.__add_entry_box(self.frames['top'], title='log_file', width=45)
        self.elements['log_file'].insert(0, f'huginn_log_{datetime.now():%Y%m%dT%H%M%S}.txt')
        log_file_button = tkinter.Button(self.frames['top'], text='...', command=self.__select_log_file)
        log_file_button.grid(row=self.last_row, column=2)

        self.toggle_text = tkinter.StringVar()
        self.toggle_text.set('Start')
        toggle_button = tkinter.Button(self.frames['top'], textvariable=self.toggle_text, command=self.toggle)
        toggle_button.grid(row=self.last_row + 1, column=1)
        self.last_row += 1

        self.__add_text_box(self.frames['bottom'], title='longitude', units='°')
        self.__add_text_box(self.frames['bottom'], title='latitude', units='°')
        self.__add_text_box(self.frames['bottom'], title='altitude', units='m')
        self.__add_text_box(self.frames['bottom'], title='ground_speed', units='m/s')
        self.__add_text_box(self.frames['bottom'], title='ascent_rate', units='m/s')

        for element in self.frames['bottom'].winfo_children():
            element.configure(state=tkinter.DISABLED)

        try:
            radio_port = radio.port()
        except OSError:
            radio_port = ''

        self.replace_text(self.elements['port'], radio_port)

        self.main_window.mainloop()

    def __add_text_box(self, frame: tkinter.Frame, title: str, units: str = None, row: int = None, entry: bool = False,
                       width: int = 10):
        if row is None:
            row = self.last_row + 1

        column = 0

        element_label = tkinter.Label(frame, text=title)
        element_label.grid(row=row, column=column)

        column += 1

        if entry:
            element = tkinter.Entry(frame, width=width)
        else:
            element = tkinter.Text(frame, width=width, height=1)

        element.grid(row=row, column=column)

        column += 1

        if units is not None:
            units_label = tkinter.Label(frame, text=units)
            units_label.grid(row=row, column=column)

        column += 1

        self.last_row = row

        self.elements[title] = element

    def __add_entry_box(self, frame: tkinter.Frame, title: str, row: int = None, width: int = 10):
        self.__add_text_box(frame, title, row=row, entry=True, width=width)

    def __select_log_file(self):
        filename = os.path.splitext(self.elements['log_file'].get())[0]
        path = tkinter.filedialog.asksaveasfilename(title='Huginn log location...', initialfile=filename,
                                                    defaultextension='.txt', filetypes=[('Text', '*.txt')])

        if path != '':
            self.replace_text(self.elements['log_file'], path)

    def toggle(self):
        if self.running:
            self.connections['radio'].close()
            logging.info(f'Closed port {self.connections["radio"].serial_port}')

            for element in self.frames['bottom'].winfo_children():
                element.configure(state=tkinter.DISABLED)

            self.toggle_text.set('Start')
            self.running = False
        else:
            try:
                self.serial_port = self.elements['port'].get()

                if self.serial_port is '':
                    serial_port = radio.port()
                    self.replace_text(self.elements['port'], serial_port)

                log_filename = self.elements['log_file'].get()
                logging.basicConfig(filename=log_filename, level=logging.INFO,
                                    datefmt='%Y-%m-%d %H:%M:%S', format='[%(asctime)s] %(levelname)s: %(message)s')
                console = logging.StreamHandler()
                console.setLevel(logging.DEBUG)
                logging.getLogger('').addHandler(console)

                self.connections['radio'] = radio.Radio(self.serial_port)
                self.serial_port = self.connections['radio'].serial_port
                logging.info(f'Opened port {self.serial_port}')

                for element in self.frames['bottom'].winfo_children():
                    element.configure(state=tkinter.ACTIVE)

                self.toggle_text.set('Stop')
                self.running = True

                self.run()
            except Exception as error:
                tkinter.messagebox.showerror('Initialization Error', error)

    def run(self):
        parsed_packets = self.connections['radio'].read()

        for parsed_packet in parsed_packets:
            callsign = parsed_packet['callsign']

            if callsign in self.packet_tracks:
                if parsed_packet not in self.packet_tracks[callsign]:
                    self.packet_tracks[callsign].append(parsed_packet)
                else:
                    logging.debug(f'Received duplicate packet: {parsed_packet}')
            else:
                self.packet_tracks[callsign] = tracks.APRSTrack(callsign, [parsed_packet])

            message = f'{parsed_packet}'

            if 'longitude' in parsed_packet and 'latitude' in parsed_packet:
                longitude, latitude, altitude = self.packet_tracks[callsign].coordinates()
                ascent_rate = self.packet_tracks[callsign].ascent_rate()
                ground_speed = self.packet_tracks[callsign].ground_speed()
                seconds_to_impact = self.packet_tracks[callsign].seconds_to_impact()
                message = f'{message} ascent_rate={ascent_rate} ground_speed={ground_speed} seconds_to_impact={seconds_to_impact}'

                if callsign in BALLOON_CALLSIGNS:
                    self.replace_text(self.elements['longitude'], longitude)
                    self.replace_text(self.elements['latitude'], latitude)
                    self.replace_text(self.elements['altitude'], altitude)
                    self.replace_text(self.elements['ground_speed'], ground_speed)
                    self.replace_text(self.elements['ascent_rate'], ascent_rate)

            logging.info(message)

        if self.running:
            self.main_window.after(1000, self.run)

    @staticmethod
    def replace_text(element, value):
        if type(element) is tkinter.Text:
            start_index = '1.0'
        else:
            start_index = 0

        element.delete(start_index, tkinter.END)
        element.insert(start_index, value)


if __name__ == '__main__':
    huginn_gui = HuginnGUI()
