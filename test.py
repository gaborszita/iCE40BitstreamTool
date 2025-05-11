from ice40bitstreamtool import create_device_config

device_config = create_device_config("chipdb/chipdb-1k.txt")
device_config.process_bitstream("../example.asc")
print(device_config.generate_bitstream())