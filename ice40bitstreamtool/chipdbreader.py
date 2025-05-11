import re
from .deviceconfig import DeviceConfig
from .filereader import read_file

def _process_chipdb_config(config_sections):
  """
  Creates a DeviceConfig object from the parsed sections of the chipdb file.

  :param config_sections: List of _FileSection objects from the chipdb file.
  :return: A DeviceConfig object created using the chipdb configuration.
  """
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

def create_device_config(path):
  """
  Creates a DeviceConfig object using a chipdb file.

  :param path: Path to the chipdb file.
  """

  return _process_chipdb_config(read_file(path, split_lines=True))