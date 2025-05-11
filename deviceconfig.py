import re
from abc import ABC, abstractmethod
from itertools import chain

class Freezable:
  def __init__(self):
    self._frozen = False

  def freeze(self):
    self._frozen = True

  def is_frozen(self):
    return self._frozen

  def _ensure_not_frozen(self):
    if self._frozen:
      raise Exception("You cannot manipulate a frozen object!")

class DeviceConfig(Freezable):
  def __init__(self, device_config_section):
    super().__init__()
    header = device_config_section.get_header()
    if len(header) != 4:
      raise Exception("Invalid device config")
    self._device_type = header[0]
    width = int(header[1])
    height = int(header[2])
    num_nets = int(header[3])
    self._tiles = [[None for _ in range(width)] for _ in range(height)]
    self._nets = [None for _ in range(num_nets)]
    self._net_nodes = dict()
    self._logic_tile_bit_config = None
    self._io_tile_bit_config = None
    self._ramb_tile_bits_config = None
    self._ramt_tile_bits_config = None
    self._frozen = False

  def _get_config_bit_coordinates(self, bit_config):
    match = re.search(r'\[(\d+)\]', bit_config)
    if match:
      x = int(match.group(1))
    else:
      raise Exception("Invalid bit config")
    match = re.search(r'B(\d+)\[', bit_config)
    if match:
      y = int(match.group(1))
    else:
      raise Exception("Invalid bit config")
    return (x, y)
  
  def process_logic_tile_bit_config(self, logic_tile_bit_config_section):
    self._ensure_not_frozen()
    header = logic_tile_bit_config_section.get_header()
    if len(header) != 2:
      print("Invalid logic tile bit config")
    width = int(header[0])
    height = int(header[1])
    carry_in_set_bit = None
    col_buf_ctrl_set_bits = [None for _ in range(8)]
    lc_set_bits = [None for _ in range(8)]
    neg_clk_set_bit = None
    for line in logic_tile_bit_config_section.get_lines():
      col_buf_ctrl_match = re.match(r"ColBufCtrl\.glb_netwk_(\d+)", line[0])
      lc_match = re.match(r"LC_(\d+)", line[0])
      if line[0] == "CarryInSet":
        carry_in_set_bit = self._get_config_bit_coordinates(line[1])
      elif col_buf_ctrl_match:
        global_netwk_num = int(col_buf_ctrl_match.group(1))
        col_buf_ctrl_set_bits[global_netwk_num] = self._get_config_bit_coordinates(line[1])
      elif lc_match:
        lc_num = int(lc_match.group(1))
        lc_set_bits[lc_num] = [self._get_config_bit_coordinates(x) for x in line[1:]]
      elif line[0] == "NegClk":
        neg_clk_set_bit = self._get_config_bit_coordinates(line[1])
    if carry_in_set_bit == None or None in col_buf_ctrl_set_bits or None in lc_set_bits or neg_clk_set_bit == None:
      raise Exception("Incomplete logic tile config")
    self._logic_tile_bit_config = LogicTileBitConfig(width, height, carry_in_set_bit, col_buf_ctrl_set_bits, lc_set_bits, neg_clk_set_bit)

  def process_io_tile_bit_config(self, io_tile_bit_config_section):
    self._ensure_not_frozen()
    header = io_tile_bit_config_section.get_header()
    if len(header) != 2:
      print("Invalid logic tile bit config")
    width = int(header[0])
    height = int(header[1])
    col_buf_ctrl_set_bits = [None for _ in range(8)]
    iob_0_pintype = [None for _ in range(6)]
    iob_1_pintype = [None for _ in range(6)]
    icegate = None
    io_ctrl_ie_0 = None
    io_ctrl_ie_1 = None
    io_ctrl_lvds = None
    io_ctrl_ren_0 = None
    io_ctrl_ren_1 = None
    negclk = None
    pll_config = [None for _ in range(9)]
    for line in io_tile_bit_config_section.get_lines():
      col_buf_ctrl_match = re.match(r"ColBufCtrl\.glb_netwk_(\d+)", line[0])
      iob_0_match = re.match(r"IOB_0\.PINTYPE_(\d+)", line[0])
      iob_1_match = re.match(r"IOB_1\.PINTYPE_(\d+)", line[0])
      pll_match = re.match(r"PLL\.PLLCONFIG_(\d+)", line[0])
      if col_buf_ctrl_match:
        global_netwk_num = int(col_buf_ctrl_match.group(1))
        col_buf_ctrl_set_bits[global_netwk_num] = self._get_config_bit_coordinates(line[1])
      elif iob_0_match:
        pintype_num = int(iob_0_match.group(1))
        iob_0_pintype[pintype_num] = self._get_config_bit_coordinates(line[1])
      elif iob_1_match:
        pintype_num = int(iob_1_match.group(1))
        iob_1_pintype[pintype_num] = self._get_config_bit_coordinates(line[1])
      elif line[0] == "Icegate":
        icegate = self._get_config_bit_coordinates(line[1])
      elif line[0] == "IoCtrl.IE_0":
        io_ctrl_ie_0 = self._get_config_bit_coordinates(line[1])
      elif line[0] == "IoCtrl.IE_1":
        io_ctrl_ie_1 = self._get_config_bit_coordinates(line[1])
      elif line[0] == "IoCtrl.LVDS":
        io_ctrl_lvds = self._get_config_bit_coordinates(line[1])
      elif line[0] == "IoCtrl.REN_0":
        io_ctrl_ren_0 = self._get_config_bit_coordinates(line[1])
      elif line[0] == "IoCtrl.REN_1":
        io_ctrl_ren_1 = self._get_config_bit_coordinates(line[1])
      elif line[0] == "NegClk":
        negclk = self._get_config_bit_coordinates(line[1])
      elif pll_match:
        pll_num = int(pll_match.group(1))
        pll_config[pll_num-1] = self._get_config_bit_coordinates(line[1])
    if None in col_buf_ctrl_set_bits or None in iob_0_pintype or None in iob_1_pintype or icegate == None or io_ctrl_ie_0 == None or io_ctrl_ie_1 == None or io_ctrl_lvds == None or io_ctrl_ren_0 == None or io_ctrl_ren_1 == None or negclk == None or None in pll_config:
      raise Exception("Incomplete IO tile config")
    self._io_tile_bit_config = IoTileBitConfig(width,
                                                height,
                                                col_buf_ctrl_set_bits,
                                                iob_0_pintype,
                                                iob_1_pintype,
                                                icegate,
                                                io_ctrl_ie_0,
                                                io_ctrl_ie_1,
                                                io_ctrl_lvds,
                                                io_ctrl_ren_0,
                                                io_ctrl_ren_1,
                                                negclk,
                                                pll_config)
  
  def process_ramb_tile_bit_config(self, ramb_tile_bits_config_section):
    self._ensure_not_frozen()
    header = ramb_tile_bits_config_section.get_header()
    if len(header) != 2:
      print("Invalid ramb tile bits config")
    width = int(header[0])
    height = int(header[1])
    col_buf_ctrl_set_bits = [None for _ in range(8)]
    negclk = None
    ram_config_powerup = None
    for line in ramb_tile_bits_config_section.get_lines():
      col_buf_ctrl_match = re.match(r"ColBufCtrl\.glb_netwk_(\d+)", line[0])
      if col_buf_ctrl_match:
        global_netwk_num = int(col_buf_ctrl_match.group(1))
        col_buf_ctrl_set_bits[global_netwk_num] = self._get_config_bit_coordinates(line[1])
      elif line[0] == "NegClk":
        negclk = self._get_config_bit_coordinates(line[1])
      elif line[0] == "RamConfig.PowerUp":
        ram_config_powerup = self._get_config_bit_coordinates(line[1])
    if None in col_buf_ctrl_set_bits or negclk == None or ram_config_powerup == None:
      raise Exception("Incomplete ramb tile bits config")
    self._ramb_tile_bits_config = RambTileBitConfig(width, height, col_buf_ctrl_set_bits, negclk, ram_config_powerup)

  def process_ramt_tile_bit_config(self, ramt_tile_bits_config_section):
    self._ensure_not_frozen()
    header = ramt_tile_bits_config_section.get_header()
    if len(header) != 2:
      print("Invalid ramt tile bits config")
    width = int(header[0])
    height = int(header[1])
    negclk = None
    ram_config_bits = [None for _ in range(4)]
    ram_cascade_bit_offset = 4 # TODO: calculate this dynamically
    ram_cascade_bits = [None for _ in range(4)]
    for line in ramt_tile_bits_config_section.get_lines():
      ram_cascade_match = re.match(r"RamCascade\.CBIT_(\d+)", line[0])
      ram_config_match = re.match(r"RamConfig\.CBIT_(\d+)", line[0])
      if line[0] == "NegClk":
        negclk = self._get_config_bit_coordinates(line[1])
      elif ram_cascade_match:
        ram_num = int(ram_cascade_match.group(1))
        ram_cascade_bits[ram_num-ram_cascade_bit_offset] = self._get_config_bit_coordinates(line[1])
      elif ram_config_match:
        ram_num = int(ram_config_match.group(1))
        ram_config_bits[ram_num] = self._get_config_bit_coordinates(line[1])
    if negclk == None or None in ram_config_bits or None in ram_cascade_bits:
      raise Exception("Incomplete ramt tile bits config")
    self._ramt_tile_bits_config = RamtTileBitConfig(width, height, negclk, ram_config_bits, ram_cascade_bits)

  def process_logic_tile(self, logic_tile_config):
    self._ensure_not_frozen()
    header = logic_tile_config.get_header()
    if len(header) != 2:
      print("Invalid logic tile config")
    x = int(header[0])
    y = int(header[1])
    self._tiles[y][x] = LogicTile(x, y, self._logic_tile_bit_config)
  
  def process_io_tile(self, io_tile_config):
    self._ensure_not_frozen()
    header = io_tile_config.get_header()
    if len(header) != 2:
      print("Invalid logic tile config")
    x = int(header[0])
    y = int(header[1])
    self._tiles[y][x] = IoTile(x, y, self._io_tile_bit_config)
  
  def process_ramb_tile(self, ramb_tile_config):
    self._ensure_not_frozen()
    header = ramb_tile_config.get_header()
    if len(header) != 2:
      print("Invalid ramb tile config")
    x = int(header[0])
    y = int(header[1])
    self._tiles[y][x] = RambTile(x, y, self._ramb_tile_bits_config)
  
  def process_ramt_tile(self, ramt_tile_config):
    self._ensure_not_frozen()
    header = ramt_tile_config.get_header()
    if len(header) != 2:
      print("Invalid ramt tile config")
    x = int(header[0])
    y = int(header[1])
    self._tiles[y][x] = RamtTile(x, y, self._ramt_tile_bits_config)
  
  def process_net(self, net_config_section):
    self._ensure_not_frozen()
    idx = int(net_config_section.get_header()[0])
    net = Net(idx)
    for alias_config in net_config_section.get_lines():
      if len(alias_config) != 3:
        raise Exception("Invalid net config")
      x = int(alias_config[0])
      y = int(alias_config[1])
      name = alias_config[2]
      if name not in self._net_nodes:
        self._net_nodes[name] = NetNode(name)
      net_nodece = self._net_nodes[name]
      self._tiles[y][x].add_net_nodes(net_nodece)
      net.add_net_node(self._tiles[y][x], net_nodece)
    self._nets[idx] = net
  
  def process_routing_switch(self, routing_switch_config_section):
    self._ensure_not_frozen()
    header = routing_switch_config_section.get_header()
    if len(header) < 4:
      print("Invalid routing switch config")
    x = int(header[0])
    y = int(header[1])
    dst_net_idx = int(header[2])
    config_bit_coordinates = []
    for elem in header[3:]:
      config_bit_coordinates.append(self._get_config_bit_coordinates(elem))
    config_bit_coordinates.reverse()
    src_net_to_bit_vals_dict = dict()
    for line in routing_switch_config_section.get_lines():
      config_bit_values = int(line[0], 2)
      src_net_idx = int(line[1])
      src_net_to_bit_vals_dict[self._nets[src_net_idx]] = config_bit_values
    routing_switch = RoutingSwitch(self._nets[dst_net_idx], config_bit_coordinates, src_net_to_bit_vals_dict)
    self._tiles[y][x].add_routing_switch(routing_switch)
  
  def process_buffer(self, buffer_config_section):
    self._ensure_not_frozen()
    header = buffer_config_section.get_header()
    if len(header) < 4:
      print("Invalid buffer config")
    x = int(header[0])
    y = int(header[1])
    dst_net_idx = int(header[2])
    config_bit_coordinates = []
    for elem in header[3:]:
      config_bit_coordinates.append(self._get_config_bit_coordinates(elem))
    config_bit_coordinates.reverse()
    src_net_to_bit_vals_dict = dict()
    for line in buffer_config_section.get_lines():
      config_bit_values = int(line[0], 2)
      src_net_idx = int(line[1])
      src_net_to_bit_vals_dict[self._nets[src_net_idx]] = config_bit_values
    buffer = Buffer(self._nets[dst_net_idx], config_bit_coordinates, src_net_to_bit_vals_dict)
    self._tiles[y][x].add_buffer(buffer)

  def get_tiles(self):
    return self._tiles.copy()

  def get_nets(self):
    return self._nets.copy()
  
  def get_net_nodes(self):
    return self._net_nodes.values()
  
  def freeze(self):
    super().freeze()
    for tile_row in self._tiles:
      for tile in tile_row:
        if tile is not None:
          tile.freeze()
    for net in self._nets:
      net.freeze()
  
  def get_config(self):
    config_string = ""
    config_string += ".device " + self._device_type + "\n"
    for y in range(len(self._tiles)):
      for x in range(len(self._tiles[y])):
        tile = self._tiles[y][x]
        if tile is not None:
          config_string += "." + tile.get_type() + " " + str(x) + " " + str(y) + "\n"
          config_string += tile.get_config() + "\n"
    return config_string.strip()

class BitConfigBuilder:
  def __init__(self, width, height):
    self._config = [[0 for _ in range(width)]for _ in range(height)]

  def set_bit(self, coord, value):
    if value == False:
      value = 0
    elif value == True:
      value = 1
    self._config[coord[1]][coord[0]] = value
  
  def get_config_string(self):
    config_string = ""
    for row in self._config:
      config_string += "".join([str(bit) for bit in row]) + "\n"
    return config_string.strip()

class Tile(ABC, Freezable):
  def __init__(self, x, y):
    Freezable.__init__(self)
    self._x = x
    self._y = y
    self._net_nodes = []
    self._routing_switches = []
    self._buffers = []

  def add_net_nodes(self, net_node):
    self._ensure_not_frozen()
    self._net_nodes.append(net_node)
  
  def add_routing_switch(self, routing_switch):
    self._ensure_not_frozen()
    self._routing_switches.append(routing_switch)
  
  def add_buffer(self, buffer):
    self._ensure_not_frozen()
    self._buffers.append(buffer)

  def _get_routing_resources_config(self, bit_config_builder):
    for routing_switch in self._routing_switches:
      config_bits = routing_switch.get_config_bits()
      for config_bit in routing_switch.get_config_bit_coordinates():
        bit_config_builder.set_bit(config_bit, config_bits & 1)
        config_bits >>= 1
    for buffer in self._buffers:
      config_bits = buffer.get_config_bits()
      for config_bit in buffer.get_config_bit_coordinates():
        bit_config_builder.set_bit(config_bit, config_bits & 1)
        config_bits >>= 1
  
  def _process_bitstream_routing_resources(self, bitstream):
    for routing_resource in chain(self._routing_switches, self._buffers):
      config_bit_coords = routing_resource.get_config_bit_coordinates()
      bit_config = 0
      bit_pos = 1
      for coord in config_bit_coords:
        if int(bitstream[coord[1]][coord[0]]) == 1:
          bit_config |= bit_pos
        bit_pos <<= 1
      routing_resource.set_config_bits(bit_config)

  @abstractmethod
  def get_type(self):
    pass

  @abstractmethod
  def get_config(self):
    pass
  
  @abstractmethod
  def process_bitstream(self, bitstream):
    pass

class LogicTile(Tile):
  def __init__(self, x, y, logic_tile_bit_config):
    super().__init__(x, y)
    self._bit_config = logic_tile_bit_config
    self.carry_in_set = 0
    self.col_buf_ctrl = 0
    self.lc_bits = [0 for _ in range(8)]
    self.neg_clk = False

  def get_config(self):
    config_builder = BitConfigBuilder(self._bit_config.width, self._bit_config.height)
    config_builder.set_bit(self._bit_config.carry_in_set_bit, self.carry_in_set)
    col_buf_ctrl = self.col_buf_ctrl
    for col_buf_ctrl_bit in self._bit_config.col_buf_ctrl_set_bits:
      config_builder.set_bit(col_buf_ctrl_bit, col_buf_ctrl & 1)
      col_buf_ctrl >>= 1
    for idx, lc_bit in enumerate(self.lc_bits):
      for lc_set_bit in self._bit_config.lc_set_bits[idx]:
        config_builder.set_bit(lc_set_bit, lc_bit & 1)
        lc_bit >>= 1
    config_builder.set_bit(self._bit_config.neg_clk_set_bit, self.neg_clk)
    self._get_routing_resources_config(config_builder)
    return config_builder.get_config_string()
  
  def get_type(self):
    return "logic_tile"
  
  def process_bitstream(self, bitstream):
    self._process_bitstream_routing_resources(bitstream)

    x, y = self._bit_config.carry_in_set_bit
    self.carry_in_set = int(bitstream[y][x])

    col_buf_ctrl = 0
    bit_pos = 1
    for coord in self._bit_config.col_buf_ctrl_set_bits:
      if int(bitstream[coord[1]][coord[0]]) == 1:
        col_buf_ctrl |= bit_pos
      bit_pos <<= 1
    self.col_buf_ctrl = col_buf_ctrl

    for idx, lc_set_bits in enumerate(self._bit_config.lc_set_bits):
      lc_config = 0
      bit_pos = 1
      for coord in lc_set_bits:
        if int(bitstream[coord[1]][coord[0]]) == 1:
          lc_config |= bit_pos
        bit_pos <<= 1
      self.lc_bits[idx] = lc_config
    
    x, y = self._bit_config.neg_clk_set_bit
    self.neg_clk = bool(int(bitstream[y][x]))

class IoTile(Tile):
  def __init__(self, x, y, io_tile_bit_config):
    super().__init__(x, y)
    self._bit_config = io_tile_bit_config
    self.col_buf_ctrl = 0
    self.iob_0_pintype = 0
    self.iob_1_pintype = 0
    self.icegate = False
    self.io_ctrl_ie_0 = False
    self.io_ctrl_ie_1 = False
    self.io_ctrl_lvds = False
    self.io_ctrl_ren_0 = False
    self.io_ctrl_ren_1 = False
    self.negclk = False
    self.pll_config = 0

  def get_config(self):
    config_builder = BitConfigBuilder(self._bit_config.width, self._bit_config.height)
    config_builder.set_bit(self._bit_config.col_buf_ctrl_set_bits[0], self.col_buf_ctrl)
    iob_0_pintype = self.iob_0_pintype
    for iob_0_pintype_bit in self._bit_config.iob_0_pintype:
      config_builder.set_bit(iob_0_pintype_bit, iob_0_pintype & 1)
      iob_0_pintype >>= 1
    iob_1_pintype = self.iob_1_pintype
    for iob_1_pintype_bit in self._bit_config.iob_1_pintype:
      config_builder.set_bit(iob_1_pintype_bit, iob_1_pintype & 1)
      iob_1_pintype >>= 1
    config_builder.set_bit(self._bit_config.icegate, self.icegate)
    config_builder.set_bit(self._bit_config.io_ctrl_ie_0, self.io_ctrl_ie_0)
    config_builder.set_bit(self._bit_config.io_ctrl_ie_1, self.io_ctrl_ie_1)
    config_builder.set_bit(self._bit_config.io_ctrl_lvds, self.io_ctrl_lvds)
    config_builder.set_bit(self._bit_config.io_ctrl_ren_0, self.io_ctrl_ren_0)
    config_builder.set_bit(self._bit_config.io_ctrl_ren_1, self.io_ctrl_ren_1)
    config_builder.set_bit(self._bit_config.negclk, self.negclk)
    pll_config = self.pll_config
    for pll_config_bit in self._bit_config.pll_config:
      config_builder.set_bit(pll_config_bit, pll_config & 1)
      pll_config >>= 1
    self._get_routing_resources_config(config_builder)
    return config_builder.get_config_string()
  
  def get_type(self):
    return "io_tile"
  
  def process_bitstream(self, bitstream):
    self._process_bitstream_routing_resources(bitstream)

    col_buf_ctrl = 0
    bit_pos = 1
    for coord in self._bit_config.col_buf_ctrl_set_bits:
      if int(bitstream[coord[1]][coord[0]]) == 1:
        col_buf_ctrl |= bit_pos
      bit_pos <<= 1
    self.col_buf_ctrl = col_buf_ctrl

    iob_0_pintype = 0
    bit_pos = 1
    for coord in self._bit_config.iob_0_pintype:
      if int(bitstream[coord[1]][coord[0]]) == 1:
        iob_0_pintype |= bit_pos
      bit_pos <<= 1
    self.iob_0_pintype = iob_0_pintype

    iob_1_pintype = 0
    bit_pos = 1
    for coord in self._bit_config.iob_1_pintype:
      if int(bitstream[coord[1]][coord[0]]) == 1:
        iob_1_pintype |= bit_pos
      bit_pos <<= 1
    self.iob_1_pintype = iob_1_pintype

    x, y = self._bit_config.icegate
    self.icegate = bool(int(bitstream[y][x]))
    x, y = self._bit_config.io_ctrl_ie_0
    self.io_ctrl_ie_0 = bool(int(bitstream[y][x]))
    x, y = self._bit_config.io_ctrl_ie_1
    self.io_ctrl_ie_1 = bool(int(bitstream[y][x]))
    x, y = self._bit_config.io_ctrl_lvds
    self.io_ctrl_lvds = bool(int(bitstream[y][x]))
    x, y = self._bit_config.io_ctrl_ren_0
    self.io_ctrl_ren_0 = bool(int(bitstream[y][x]))
    x, y = self._bit_config.io_ctrl_ren_1
    self.io_ctrl_ren_1 = bool(int(bitstream[y][x]))
    x, y = self._bit_config.negclk
    self.negclk = bool(int(bitstream[y][x]))

    pll_config = 0
    bit_pos = 1
    for coord in self._bit_config.pll_config:
      if int(bitstream[coord[1]][coord[0]]) == 1:
        pll_config |= bit_pos
      bit_pos <<= 1
    self.pll_config = pll_config

class RambTile(Tile):
  def __init__(self, x, y, ramb_tile_bit_config):
    super().__init__(x, y)
    self._ramb_tile_bit_config = ramb_tile_bit_config
    self.col_buf_ctrl = 0
    self.negclk = False
    self.ram_config_powerup = False
  
  def get_config(self):
    config_builder = BitConfigBuilder(self._ramb_tile_bit_config.width, self._ramb_tile_bit_config.height)
    col_buf_ctrl = self.col_buf_ctrl
    for col_buf_ctrl_bit in self._ramb_tile_bit_config.col_buf_ctrl_set_bits:
      config_builder.set_bit(col_buf_ctrl_bit, col_buf_ctrl & 1)
      col_buf_ctrl >>= 1
    config_builder.set_bit(self._ramb_tile_bit_config.negclk, self.negclk)
    config_builder.set_bit(self._ramb_tile_bit_config.ram_config_powerup, self.ram_config_powerup)
    self._get_routing_resources_config(config_builder)
    return config_builder.get_config_string()

  def get_type(self):
    return "ramb_tile"

  def process_bitstream(self, bitstream):
    self._process_bitstream_routing_resources(bitstream)

    col_buf_ctrl = 0
    bit_pos = 1
    for coord in self._ramb_tile_bit_config.col_buf_ctrl_set_bits:
      if int(bitstream[coord[1]][coord[0]]) == 1:
        col_buf_ctrl |= bit_pos
      bit_pos <<= 1
    self.col_buf_ctrl = col_buf_ctrl

    x, y = self._ramb_tile_bit_config.negclk
    self.negclk = bool(int(bitstream[y][x]))
    x, y = self._ramb_tile_bit_config.ram_config_powerup
    self.ram_config_powerup = bool(int(bitstream[y][x]))

class RamtTile(Tile):
  def __init__(self, x, y, ramt_tile_bit_config):
    super().__init__(x, y)
    self._ramt_tile_bit_config = ramt_tile_bit_config
    self.negclk = False
    self.ram_config = 0
    self.ram_cascade = 0
  
  def get_config(self):
    config_builder = BitConfigBuilder(self._ramt_tile_bit_config.width, self._ramt_tile_bit_config.height)
    config_builder.set_bit(self._ramt_tile_bit_config.negclk, self.negclk)
    ram_config = self.ram_config
    for ram_config_bit in self._ramt_tile_bit_config.ram_config_bits:
      config_builder.set_bit(ram_config_bit, ram_config & 1)
      ram_config >>= 1
    ram_cascade = self.ram_cascade
    for ram_cascade_bit in self._ramt_tile_bit_config.ram_cascade_bits:
      config_builder.set_bit(ram_cascade_bit, ram_cascade & 1)
      ram_cascade >>= 1
    self._get_routing_resources_config(config_builder)
    return config_builder.get_config_string()
  
  def get_type(self):
    return "ramt_tile"

  def process_bitstream(self, bitstream):
    self._process_bitstream_routing_resources(bitstream)

    x, y = self._ramt_tile_bit_config.negclk
    self.negclk = bool(int(bitstream[y][x]))

    ram_config = 0
    bit_pos = 1
    for coord in self._ramt_tile_bit_config.ram_config_bits:
      if int(bitstream[coord[1]][coord[0]]) == 1:
        ram_config |= bit_pos
      bit_pos <<= 1
    self.ram_config = ram_config

    ram_cascade = 0
    bit_pos = 1
    for coord in self._ramt_tile_bit_config.ram_cascade_bits:
      if int(bitstream[coord[1]][coord[0]]) == 1:
        ram_cascade |= bit_pos
      bit_pos <<= 1
    self.ram_cascade = ram_cascade

class TileBitConfig:
  def __init__(self, width, height):
    self.width = width
    self.height = height

class LogicTileBitConfig(TileBitConfig):
  def __init__(self, width, height, carry_in_set_bit, col_buf_ctrl_set_bits, lc_set_bits, neg_clk_set_bit):
    super().__init__(width, height)
    self.carry_in_set_bit = carry_in_set_bit
    self.col_buf_ctrl_set_bits = col_buf_ctrl_set_bits
    self.lc_set_bits = lc_set_bits
    self.neg_clk_set_bit = neg_clk_set_bit

class IoTileBitConfig(TileBitConfig):
  def __init__(self, width, height, col_buf_ctrl_set_bits, iob_0_pintype, iob_1_pintype, icegate, io_ctrl_ie_0, io_ctrl_ie_1, io_ctrl_lvds, io_ctrl_ren_0, io_ctrl_ren_1, negclk, pll_config):
    super().__init__(width, height)
    self.width = width
    self.height = height
    self.col_buf_ctrl_set_bits = col_buf_ctrl_set_bits
    self.iob_0_pintype = iob_0_pintype
    self.iob_1_pintype = iob_1_pintype
    self.icegate = icegate
    self.io_ctrl_ie_0 = io_ctrl_ie_0
    self.io_ctrl_ie_1 = io_ctrl_ie_1
    self.io_ctrl_lvds = io_ctrl_lvds
    self.io_ctrl_ren_0 = io_ctrl_ren_0
    self.io_ctrl_ren_1 = io_ctrl_ren_1
    self.negclk = negclk
    self.pll_config = pll_config

class RambTileBitConfig(TileBitConfig):
  def __init__(self, width, height, col_buf_ctrl_set_bits, negclk, ram_config_powerup):
    super().__init__(width, height)
    self.width = width
    self.height = height
    self.col_buf_ctrl_set_bits = col_buf_ctrl_set_bits
    self.negclk = negclk
    self.ram_config_powerup = ram_config_powerup

class RamtTileBitConfig(TileBitConfig):
  def __init__(self, width, height, negclk, ram_config_bits, ram_cascade_bits):
    super().__init__(width, height)
    self.width = width
    self.height = height
    self.negclk = negclk
    self.ram_config_bits = ram_config_bits
    self.ram_cascade_bits = ram_cascade_bits

class NetNode:
  def __init__(self, name):
    self._name = name

class Net(Freezable):
  def __init__(self, index):
    super().__init__()
    self._index = index
    self._net_nodes = dict()
    self._frozen = False
  
  def add_net_node(self, tile, net_node):
    self._ensure_not_frozen()
    self._net_nodes[tile] = net_node
    
class RoutingResource:
  def __init__(self, dst_net, config_bit_coordinates, src_net_to_bit_vals_dict):
    self._dst_net = dst_net
    self._config_bit_coordinates = config_bit_coordinates
    self._src_net_to_bit_vals_dict = src_net_to_bit_vals_dict
    self._connection = None
  
  def connect(self, src_net):
    if src_net not in self._src_net_to_bit_vals_dict:
      raise Exception("Invalid source net")
    self._connection = src_net
  
  def disconnect(self):
    self._connection = None
  
  def get_config_bits(self):
    if self._connection is None:
      return 0
    else:
      return self._src_net_to_bit_vals_dict[self._connection]
  
  def set_config_bits(self, bit_config):
    if bit_config == 0:
      self._connection = None
    else:
      found_net = False
      for src_net, bit_vals in self._src_net_to_bit_vals_dict.items():
        if bit_vals == bit_config:
          self._connection = src_net
          found_net = True
          break
      if found_net == False:
        raise Exception("Invalid routing resource bit config")
  
  def get_config_bit_coordinates(self):
    return self._config_bit_coordinates

class RoutingSwitch(RoutingResource):
  pass

class Buffer(RoutingResource):
  pass