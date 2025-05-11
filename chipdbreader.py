import re
from deviceconfig import DeviceConfig

class _FileSection:
  """
  Represents a section in the chipdb config
  """

  def __init__(self, header_line, split_lines):
    header_line_splitted = header_line.split(" ")
    self._section_type = header_line_splitted[0][1:]
    self._header = header_line_splitted[1:]
    self._split_lines = split_lines
    self._lines = []
  
  def add_line(self, line):
    if self._split_lines:
      self._lines.append(line.split(" "))
    else:
      self._lines.append(line)

  def get_type(self):
    return self._section_type
  
  def get_header(self):
    return self._header

  def get_lines(self):
    return self._lines

def _read_file(path, split_lines):
  """
  Reads a chipdb or an ASCII bitstream and returns an array of FileSections

  :param path: path of the file
  """

  sections = []
  f = open(path, "r")

  for line in f:
    line = line.strip() # remove \n at the end of the line
    # skip if a blank line or comment
    if line == "" or line.startswith("#"):
      continue
    # start of new config section
    if line.startswith("."):
      section = _FileSection(line, split_lines)
      sections.append(section)
    else:
      section.add_line(line)

  sections.append(section)
  f.close()

  return sections

def _process_chipdb_config(config_sections):
  pins_config_sections = []
  gbufin_config_sections = []
  gbufpin_config_sections = []
  iolatch_config_sections = []
  ieren_config_sections = []
  colbuf_config_sections = []
  io_tile_config_sections = []
  logic_tile_config_sections = []
  ramb_tile_config_sections = []
  ramt_tile_config_sections = []
  dsp_tile_config_sections = []
  ipcon_tile_config_sections = []
  extra_cell_config_sections = []
  extra_bits_config_sections = []
  net_config_sections = []
  buffer_config_sections = []
  routing_switch_config_sections = []
  device_config_section = None
  logic_tile_bits_config_section = None
  io_tile_bits_config_section = None
  ramb_tile_bits_config_section = None
  ramt_tile_bits_config_section = None
  for section in config_sections:
    section_type = section.get_type()
    if section_type == "device":
      device_config_section = section
    elif section_type == "pins":
      pass
    elif section_type == "gbufin":
      pass
    elif section_type == "gbufpin":
      pass
    elif section_type == "iolatch":
      pass
    elif section_type == "ieren":
      pass
    elif section_type == "colbuf":
      pass
    elif section_type == "io_tile":
      io_tile_config_sections.append(section)
    elif section_type == "logic_tile":
      logic_tile_config_sections.append(section)
    elif section_type == "ramb_tile":
      ramb_tile_config_sections.append(section)
    elif section_type == "ramt_tile":
      ramt_tile_config_sections.append(section)
    elif section_type == "ipcon_tile":
      pass
    elif section_type == "io_tile_bits":
      io_tile_bits_config_section = section
    elif section_type == "logic_tile_bits":
      logic_tile_bits_config_section = section
    elif section_type == "ramb_tile_bits":
      ramb_tile_bits_config_section = section
    elif section_type == "ramt_tile_bits":
      ramt_tile_bits_config_section = section
    elif re.match("dsp[0..3]_tile_bits", section_type):
      pass
    elif section_type == "ipcon_tile_bits":
      pass
    elif section_type == "extra_cell":
      pass
    elif section_type == "extra_bits":
      pass
    elif section_type == "net":
      net_config_sections.append(section)
    elif section_type == "buffer":
      buffer_config_sections.append(section)
    elif section_type == "routing":
      routing_switch_config_sections.append(section)
    else:
      raise Exception("Invalid config section type: " + section_type)

  if device_config_section is None:
    raise Exception("Device config section not found")
  device_config = DeviceConfig(device_config_section)

  if logic_tile_bits_config_section is None:
    raise Exception("Logic tile bit config not found")
  device_config.process_logic_tile_bit_config(logic_tile_bits_config_section)

  if io_tile_bits_config_section is None:
    raise Exception("IO tile bit config not found")
  device_config.process_io_tile_bit_config(io_tile_bits_config_section)

  if ramb_tile_bits_config_section is None:
    raise Exception("Ramb tile bit config not found")
  device_config.process_ramb_tile_bit_config(ramb_tile_bits_config_section)

  if ramt_tile_bits_config_section is None:
    raise Exception("Ramt tile bit config not found")
  device_config.process_ramt_tile_bit_config(ramt_tile_bits_config_section)

  for logic_tile_config_section in logic_tile_config_sections:
    device_config.process_logic_tile(logic_tile_config_section)
  
  for io_tile_config_section in io_tile_config_sections:
    device_config.process_io_tile(io_tile_config_section)

  for ramb_tile_config_section in ramb_tile_config_sections:
    device_config.process_ramb_tile(ramb_tile_config_section)
  
  for ramt_tile_config_section in ramt_tile_config_sections:
    device_config.process_ramt_tile(ramt_tile_config_section)

  for net_config_section in net_config_sections:
    device_config.process_net(net_config_section)
  
  for routing_switch_config_section in routing_switch_config_sections:
    device_config.process_routing_switch(routing_switch_config_section)

  for buffer_config_section in buffer_config_sections:
    device_config.process_buffer(buffer_config_section)
  
  device_config.freeze()
  
  return device_config

def process_chipdb_file(path):
  """
  Reads a chipdb and returns a DeviceConfig object

  :param path: path of the chipdb file
  """

  return _process_chipdb_config(_read_file(path, split_lines=True))

def process_bitstream(device_config, path):
  tiles = device_config.get_tiles()
  file_sections = _read_file(path, split_lines=False)
  for section in file_sections:
    tile_match = re.match(r"(io|logic|ramb|ramt)_tile", section.get_type())
    if tile_match:
      header = section.get_header()
      if len(header) != 2:
        print("Invalid logic tile config")
      x = int(header[0])
      y = int(header[1])
      tile = tiles[y][x]
      if tile.get_type() != section.get_type():
        raise Exception("Tile type mismatch between device and bitstream. " +
                        "Device has " + tile.get_type() + " at (" + str(x) + ", " + str(y) + ") "
                        "but bitstream has " + section.get_type() + " at this location.")
      tile.process_bitstream(section.get_lines())
    #print("section")

if __name__ == "__main__":
  device_config = process_chipdb_file("chipdb/chipdb-1k.txt")
  #print(device_config.get_config())
  process_bitstream(device_config, "../example.asc")
  print(device_config.get_config())
  #device_config.get_config()