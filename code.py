# Example of accessing the Person Sensor from Useful Sensors on a Pico using
# CircuitPython. See https://usfl.ink/ps_dev for the full developer guide.
# This code modified from example code at https://github.com/usefulsensors/person_sensor_circuit_python
# The main difference is that the output is written to an OLED device over I2C.

import board
import busio
import struct
import time
import adafruit_ssd1306


# The person sensor has the I2C ID of hex 62, or decimal 98.
PERSON_SENSOR_I2C_ADDRESS = 0x62

# We will be reading raw bytes over I2C, and we'll need to decode them into
# data structures. These strings define the format used for the decoding, and
# are derived from the layouts defined in the developer guide.
PERSON_SENSOR_I2C_HEADER_FORMAT = "BBH"
PERSON_SENSOR_I2C_HEADER_BYTE_COUNT = struct.calcsize(
    PERSON_SENSOR_I2C_HEADER_FORMAT)

PERSON_SENSOR_FACE_FORMAT = "BBBBBBbB"
PERSON_SENSOR_FACE_BYTE_COUNT = struct.calcsize(PERSON_SENSOR_FACE_FORMAT)

PERSON_SENSOR_FACE_MAX = 4
PERSON_SENSOR_RESULT_FORMAT = PERSON_SENSOR_I2C_HEADER_FORMAT + \
    "B" + PERSON_SENSOR_FACE_FORMAT * PERSON_SENSOR_FACE_MAX + "H"
PERSON_SENSOR_RESULT_BYTE_COUNT = struct.calcsize(PERSON_SENSOR_RESULT_FORMAT)

# How long to pause between sensor polls.
PERSON_SENSOR_DELAY = 0.2

# Instantiate two I2C buses - one for the person sensor
i2c_person = busio.I2C(scl=board.GP5, sda=board.GP4)
# and the other for the OLED.
i2c_oled = busio.I2C(scl=board.GP7, sda=board.GP6)

oled = adafruit_ssd1306.SSD1306_I2C(128, 64, i2c_oled,addr=0x3c)


def blank_oled():
  """Sets the OLED screen to black.
  """
  oled.fill(0)
  oled.show()

def show_text(text, line):
  """
  Displays the string on the OLED device in the upper left hand
  corner.
  """
  oled.fill(0)
  oled.text(text, 0, line * 10, 1)
  oled.show()


def show_faces(faces):
  """Displays the output from the PersonSensor on the oled
  device. 
  """
  oled.fill(0)
  oled.text(f'Number of faces {len(faces)}', 0, 0, 1)
  counter = 0
  for face in faces:
    counter += 1
    x0 = face["box_left"]
    y0 = face["box_top"]
    x1 = face["box_right"]
    y1 = face["box_bottom"]
    confidence = face["box_confidence"]

    facing = 'False'
    if face['is_facing'] == 1:
      facing = 'True'

    #face_text = f'{counter}: ({x0}, {y0}), ({x1,} {y1})'
    face_text = str(counter) + ':conf=' + str(confidence) + ",Facing=" + facing
    face_location = "  (" + str(x0) + "," + str(y0) + '), (' + str(x1) + ',' + str(y1) + ')'
    print(face_text)
    print(face_location)

    # if face["is_facing"]:
    #     face_text + ": facing"
    y_offset = counter * 20
    oled.text(face_text, 0, y_offset, 1)
    oled.text(face_location, 0, y_offset + 10, 1)
  oled.show()
      


blank_oled()
oled.text("Person Sensor", 0, 0, 1)
oled.show()

# oled.fill(1)
# oled.show()

# For debugging purposes print out the peripheral addresses on the I2C bus.
# 98 (0x62 in hex) is the address of our person sensor, and should be
# present in the list. Uncomment the following three lines if you want to see
# what I2C addresses are found.
# This is what is found: [57, 60, 79, 98]
# while True:
#    print(i2c.scan())
#    print('i am here')
#    time.sleep(PERSON_SENSOR_DELAY)

def lock_i2c():
  """Locks the I2C bus. The PersonSensor seems to require
  the bus to be locked before the readfrom_into() method will
  return.
  """
  while not i2c_person.try_lock():
      pass
# Unlock the I2C bus
def unlock_i2c():
  """Unlocks the I2C bus
  """
  i2c_person.unlock()

try:
  lock_i2c()
  # Keep looping and reading the person sensor results.
  while True:

      read_data = bytearray(PERSON_SENSOR_RESULT_BYTE_COUNT)
      i2c_person.readfrom_into(PERSON_SENSOR_I2C_ADDRESS, read_data)


      offset = 0
      (pad1, pad2, payload_bytes) = struct.unpack_from(
          PERSON_SENSOR_I2C_HEADER_FORMAT, read_data, offset)
      offset = offset + PERSON_SENSOR_I2C_HEADER_BYTE_COUNT

      (num_faces) = struct.unpack_from("B", read_data, offset)
      num_faces = int(num_faces[0])
      offset = offset + 1

      faces = []
      for i in range(num_faces):
          (box_confidence, box_left, box_top, box_right, box_bottom, id_confidence, id,
          is_facing) = struct.unpack_from(PERSON_SENSOR_FACE_FORMAT, read_data, offset)
          offset = offset + PERSON_SENSOR_FACE_BYTE_COUNT
          face = {
              "box_confidence": box_confidence,
              "box_left": box_left,
              "box_top": box_top,
              "box_right": box_right,
              "box_bottom": box_bottom,
              "id_confidence": id_confidence,
              "id": id,
              "is_facing": is_facing,
          }
          faces.append(face)
      checksum = struct.unpack_from("H", read_data, offset)

      show_faces(faces)

      time.sleep(PERSON_SENSOR_DELAY)

except Exception as ex:
  print(ex)
  unlock_i2c()
  
