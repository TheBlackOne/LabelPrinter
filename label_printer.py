import copy
import re as regex
import time
from decimal import Decimal

import requests
import serial
import yaml

with open("config.yaml", 'r') as config_file:
    config = yaml.safe_load(config_file)

url = config["url"]
request_payload = config["request_payload"]
skip_first_line = config["skip_first_line"]

fest = Decimal(config["fest"])
axial = Decimal(config["axial"])
radial = Decimal(config["radial"])
radial_threshold = Decimal(config["radial_threshold"])

additional_text_20 = config["additional_text_20"]
p = regex.compile(config["regex_string"])


def parse_data(text):
    parsed_data = {}

    for group in p.findall(text):
        parsed_data[group[0].strip()] = group[1]

    return parsed_data


def print_label(text):
    text = '\n'.join([line for line in text.split('\r') if line.strip()])

    final_request_payload = request_payload.copy()

    parsed_data = parse_data(text)
    a = int(parsed_data.get('A', 0))

    if a == 20:
        z = Decimal(parsed_data.get('Z', 0.0))

        fest_string = "{:.3f}".format(fest + z)
        axial_string = "{:.3f}".format(axial + z)
        radial_string = "{:.3f}".format(radial + z)

        if z >= radial_threshold:
            radial_string = "!!!"

        text += additional_text_20.format(fest_string,
                                          axial_string, radial_string)
        final_request_payload["font_size"] = 30

    if skip_first_line:
        text = '\n'.join(text.split('\n')[1:])

    final_request_payload["text"] = text

    # print(text)

    response = requests.post(url, final_request_payload)
    # print(response.status_code)
    # print(response.text)


if __name__ == "__main__":
    com_port_name = config["com_port_name"]
    baud = config["baud"]
    ser = serial.Serial(com_port_name, baud)

    page_end_chr = chr(config["page_end_ascii"])

    data_str = ""

    print_label('\r\rTN  : --------  A : 20\rX D :    -0.814 mm Abs \rZ   :    58.739 mm Abs \r')

    while (True):
        if (ser.inWaiting() > 0):
            data_str += ser.read(ser.inWaiting()).decode('ascii')

            pos_0x04 = data_str.find(page_end_chr)
            if pos_0x04 > -1:
                data_to_print = data_str[:pos_0x04]
                print_label(data_to_print)
                data_str = ""

        time.sleep(0.1)
