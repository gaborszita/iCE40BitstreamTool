class FileSection:
  """
  Represents a section in the chipdb or bitstream file.
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

def read_file(path, split_lines):
  """
  Reads a chipdb or ASCII bitstream file and parses it into sections.

  Sections start with lines beginning with a dot (e.g., '.device').
  Comment lines and blank lines are ignored.

  :param path: Path to the file to be read.
  :param split_lines: If True, entry lines are split by whitespace.
  :return: A list of _FileSection objects.
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
      section = FileSection(line, split_lines)
      sections.append(section)
    else:
      section.add_line(line)

  sections.append(section)
  f.close()

  return sections