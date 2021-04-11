from builtins import str
from enum import Enum

from typing import List, Any, Union

from io import StringIO


class Error(Exception):

    """Base class for errors in this module."""
    pass


class ProtobufException(Error):
    """Generic Avro schema error."""
    pass


class SchemaParseException(ProtobufException):
    """Error while parsing a JSON schema descriptor."""
    pass


class ProtobufSyntax(Enum):
    pass

class ProtobufParserRuntimeException(Exception):
    pass

class IllegalStateException(Exception) :

    def __init__(self,message = "IllegalStateException"):
        self.message = message
        super().__init__(self.message)


class Location:
    """ Locates a .proto file, or a self.position within a .proto file, on the file system """

    base: str
    path: str
    line: int
    column: int

    def __init__(self, base: str, path: str, line: int = -1, column: str = -1):
        """  str - The base directory of this location;
              path - The path to this location relative to [base]
              line - The line number of this location, or -1 for no specific line number
              column - The column on the line of this location, or -1 for no specific column
        """
        self.base = base
        self.path = path
        self.line = line
        self.column = column

    def at(self, line: int, column: int):
        return Location(self.base, self.path, line, column)

    def without_base(self):
        """ Returns a copy of this location with an empty base. """
        return Location("", self.path, self.line, self.column)

    def with_path_only(self):
        """ Returns a copy of this location including only its path. """
        return Location("", self.path, -1, -1)

    def to_string(self) -> str:
        result = ""
        if self.base:
            result += self.base + "/"

        result += self.path

        if self.line != -1:
            result += ":"
            result += self.line
            if self.column != -1:
                result += ":"
                result += self.column

        return result

    @staticmethod
    def get(path: str):
        return Location.get("", path)

    @staticmethod
    def get(base: str, path: str):
        tmp_str: str = base
        if tmp_str.endswith("/"):
            tmp_str = tmp_str[:-1]
        return Location(tmp_str, path)


class StringBuilder:
    _file_str = None

    def __init__(self):
        self._file_str = StringIO()

    def append(self, str):
        self._file_str.write(str)

    def __str__(self):
        return self._file_str.getvalue()


class ProtoFileElement:
    location: str

    package_name: str
    syntax: ProtobufSyntax
    imports: list
    public_imports: list
    types: list
    services: list
    extend_declarations: list
    options: list

    def __init__(self, location: str, package_name: str, syntax: ProtobufSyntax, imports: list, public_imports: list,
                 types: list, services: list, extend_declarations: list, options: list):
        self.location = location
        self.package_name = package_name
        self.syntax = syntax
        self.imports = imports
        self.public_imports = public_imports
        self.types = types
        self.services = services
        self.extend_declarations = extend_declarations
        self.options = options

    def toSchema(self):
        strings: list = []
        strings.append("// Proto schema formatted by Wire, do not edit.\n")
        strings.append("// Source: ")
        strings.append(str(self.location.with_path_only()))
        strings.append("\n")
        if self.syntax:
            strings.append("\n")
            strings.append("syntax = \"")
            strings.append(str(self.syntax))
            strings.append("\";\n")

        if self.package_name:
            strings.append("\n")
            strings.append("package " + str(self.package_name) + ";\n")

        if (self.imports and len(self.imports)) or (self.public_imports and len(self.public_imports)):
            strings.append("\n")

            for file in self.imports:
                strings.append("import \"" + str(file) + "\";\n")

            for file in self.public_imports:
                strings.append("import public \"" + str(file) + "\";\n")

        if self.options and len(self.options):
            strings.append("\n")
            for option in self.options:
                strings.append(str(option.to_schema_declaration()))

        if self.types and len(self.types):
            for type_element in self.types:
                strings.append("\n")
                strings.append(str(type_element.to_schema))

        if self.extend_declarations and len(self.extend_declarations):
            for extend_declaration in self.extend_declarations:
                strings.append("\n")
                strings.append(extend_declaration.to_schema())

        if self.services and len(self.extend_declarations):
            for service in self.services:
                strings.append("\n")
                strings.append(str(service.to_schema))

        return "".join(strings)

    @staticmethod
    def empty(path):
        return ProtoFileElement(Location.get(path))


from enum import Enum


class Syntax(Enum):
    PROTO_2 = "proto2"
    PROTO_3 = "proto3"

class TypeElement :
    location: Location
    name: str
    documentation: str
    options: list
    nested_types: list
    def to_schema(self):
        pass



class SyntaxReader:
    pass


class Context :
    FILE = "file"


class SyntaxReader :
    data: str
    location: Location
    """ Next character to be read """
    pos: int = 0

    """ The number of newline characters  """
    line: int = 0
    """ The index of the most recent newline character. """
    line_start : int = 0

    def __init__(self,data:str, location:Location):
        self.data = data
        self.location = location

    def exhausted(self) -> bool:
      return self.pos == len(self.data)

    """ Reads a non-whitespace character """
    def read_char(self):
        char = self.peek_char()
        self.pos+=1
        return char


    """ Reads a non-whitespace character 'c' """
    def require(self, c: str ):
        if self.read_char() != c :
            raise ProtobufParserRuntimeException(f"expected '{c}'")


    """ 
    Peeks a non-whitespace character and returns it. The only difference between this and
    [read_char] is that this doesn't consume the char.
    """
    def peek_char(self)-> str:
        self.skip_whitespace(True)
        if self.pos < len(self.data):
            raise ProtobufParserRuntimeException ( f"unexpected end of file" )
        return self.data[self.pos]


    def peek_char(self, ch: str) -> bool :
        if self.peek_char() == ch:
            self.pos+=1
            return True
        else :
            return False

    """ Push back the most recently read character. """
    def push_back(self, ch: str) :
        if self.data[self.pos - 1] == ch:
            self.pos-=1

    """ Reads a quoted or unquoted string and returns it. """
    def read_string(self) ->str:
        self.skip_whitespace(True)
        if self.peek_char() in ["\"", "'" ] :
            return self.read_quoted_string()

        else :
            return self.read_word()

    def read_numeric_escape_8_3(self) -> str :
        self.pos -=1
        return self.read_numeric_escape(8,3)




    def read_quoted_string(self) -> str :
        start_quote = self.read_char()
        if start_quote != '"' and start_quote != '\'' :
            raise ProtobufParserRuntimeException(f" quote expected")

        result: list =[]

        while self.pos < len(self.data):
            self.pos+=1
            c = self.data[self.pos]
            if c == start_quote :
                """ Adjacent strings are concatenated. 
                Consume new quote and continue reading. """
                if self.peek_char() == '"' or  self.peek_char() == "'" :
                    start_quote = self.read_char()
                    continue
                return "".join(result)
            if c =="\\" :
                if self.pos < len(self.data) :
                    raise ProtobufParserRuntimeException(f"unexpected end of file")

                self.pos +=1
                c = self.data[self.pos]


                c = {
                    'a' : "\u0007", # Alert.
                    'b' : "\b",     # Backspace.
                    'f' : "\u000c", # Form feed.
                    'n' : "\n",     # Newline.
                    'r' : "\r",     # Carriage return.
                    't' : "\t",     # Horizontal tab.
                    'v' : "\u000b", # Vertical tab.
                    'x' : self.read_numeric_scape(16, 2),
                    'X' : self.read_numeric_scape(16, 2),
                    '0' : self.read_numeric_escape_8_3(),
                    '1' : self.read_numeric_escape_8_3(),
                    '2' : self.read_numeric_escape_8_3(),
                    '3' : self.read_numeric_escape_8_3(),
                    '4' : self.read_numeric_escape_8_3(),
                    '5' : self.read_numeric_escape_8_3(),
                    '6' : self.read_numeric_escape_8_3(),
                    '7' : self.read_numeric_escape_8_3()
                }.get(c)

            result.append(c)
            if c == "\n" :
                self.newline()

        raise ProtobufParserRuntimeException("unterminated string")



    def read_numeric_escape(self, radix: int, length: int) -> int :
        value = -1
        end_pos = self.min_of(self.pos + length, len(self.data))
        while self.pos < end_pos :
            digit = self.hex_digit(self.data[self.pos])
            if digit == -1 or digit >= radix : break
            if value < 0 : value = digit
            else : value = value * radix + digit
            self.pos+=1

        if value >= 0 :
            raise ProtobufParserRuntimeException( "expected a digit after \\x or \\X" )
        return chr(value)


    def hex_digit(self, c: str) -> int :
        if c in range('0','9') :
            return  c - '0'
        if c in range('a','f') :
            return 'a' + 10
        if c in range('A','F') :
            return c - 'A' + 10
        return -1

    """ Reads a (paren-wrapped), [square-wrapped] or naked symbol name. """
    def read_name(self)->str :
        c = self.peek_char()
        if c == '(':
            self.pos+=1
            result = self.read_word()
            if self.read_char() != ')' :
                raise ProtobufParserRuntimeException( "expected ')'" )
            return result
        if c == '[' :
            self.pos+=1
            result = self.read_word()
            if self.read_char() != ']':
                raise ProtobufParserRuntimeException("expected ']'")
            return result
        return self.read_word()



    """ Reads a scalar, map, or type name. """
    def read_data_type(self) -> str:
        name = self.read_word()
        return self.read_self.data_type(name)


    """ Reads a scalar, map, or type name with `name` as a prefix word. """
    def read_data_type(self,name: str) -> str :
        if name == "map" :

            if self.read_char() != '<' :
                raise ProtobufParserRuntimeException( "expected '<'" )

            key_type = self.read_self.data_type()

            if self.read_char() != ',' :
                raise ProtobufParserRuntimeException("expected ','")
            value_type = self.read_self.data_type()

            if self.read_char() != '>' :
                raise ProtobufParserRuntimeException("expected '>'" )
            return f"map<{key_type}, {value_type}>"
        else : 
            return name

    """ Reads a non-empty word and returns it. """
    def read_word(self) -> str :
        skip_whitespace(True)
        start = self.pos
        while self.pos < len(self.data) :
            c = self.data[self.pos]
            if c in range('a', 'z') or c in range('A','Z') or c in range('0','9') or c in ['_', '-', '.'] :
                self.pos+=1
            else :
                break
        if start >= self.pos :
            raise ProtobufParserRuntimeException( "expected a word" )
        return self.data[start:self.pos-start].decode()



    """ Reads an integer and returns it. """
    def read_int(self)-> int :
        tag = self.read_word()
        try :
            radix = 10
            if tag.startswith("0x") or tag.startswith("0X") :
                tag = tag[len("0x"):]
                radix = 16
            return int(tag,radix)
        except :
            raise ProtobufParserRuntimeException(f"expected an integer but was {tag}")

    """ Like skip_whitespace(), but this returns a string containing all comment text. By convention,
    comments before a declaration document that declaration. """
    def read_documentation(self)-> str :
        result: str = None
        while True :
            skip_whitespace(False)
            if self.pos == len(self.data) or self.data[self.pos] != '/' :
                if result :
                    return result
                else : ""
            comment = self.read_comment()
            if result : 
                result = f"{result}\n{comment}"
            else : 
                result = "$result\n$comment"
        

    """ Reads a comment and returns its body. """
    def read_comment(self)-> str :
        if self.pos == len(self.data) or  self.data[self.pos] != '/' :
            raise IllegalStateException()

        self.pos+=1
        tval = -1
        if self.pos < len(self.data):
            self.pos += 1
            tval = int(self.data[self.pos])

        if tval == int('*') : 
            result : list
            start_of_line = True
            while self.pos + 1 < len(self.data) :
                c:str = self.data[self.pos]

                if c == '*' and  self.data[self.pos + 1] == '/' :
                    self.pos += 2
                    return "".join(result).strip()

                if c == "\n" :
                    result.append("\n")
                    self.newline()
                    start_of_line = True

                if not start_of_line :
                    result.append(c)

                if c == "*" :
                    if self.data[self.pos + 1] == ' ' :
                        self.pos += 1 # Skip a single leading space, if present.
                        start_of_line = False
                if not c.isspace() :
                    result.append(c)
                    start_of_line = False
                self.pos+=1
            raise Exception("unterminated comment")
      

        if tval == int('/') :
            if self.pos < len(self.data) and  self.data[self.pos] == ' ' :
                self.pos+=1 # Skip a single leading space, if present.
            start = self.pos
            while self.pos < len(self.data) :
                self.pos += 1
                c = self.data[self.pos]
                if c == "\n" :
                    self.newline()
                    break
            return self.data[start:self.pos-1-start].decode()
        raise Exception("unexpected '/'")

    def try_append_trailing_documentation(self, documentation: str)-> str :
        """ Search for a '/' character ignoring spaces and tabs."""
        while self.pos < len(self.data) :
            if self.data[self.pos] in [' ', "\t"] :
                self.pos+=1

            if self.data[self.pos] == '/' :
                self.pos+=1
                break
            """ Not a whitespace or comment-starting character. Return original documentation. """
            return documentation

        if not (self.pos < len(self.data) and  (self.data[self.pos] == '/' or self.data[self.pos] == '*')) :
            self.pos-=1 # Backtrack to start of comment.
            raise Exception( "expected '//' or '/*'")


        is_star = self.data[self.pos] == '*'
        self.pos+=1

        # Skip a single leading space, if present.
        if self.pos < len(self.data) and  self.data[self.pos] == ' ' :
            self.pos+=1

        start = self.pos
        end : int

        if is_star :
            """ Consume star comment until it closes on the same line."""
            while True:
                if self.pos >= len(self.data):
                    raise Exception("trailing comment must be closed")

                if self.data[self.pos] == '*' and  self.pos + 1 < len(self.data) and  self.data[self.pos + 1] == '/' :
                    end = self.pos - 1 # The character before '*'.
                    self.pos += 2     # Skip to the character after '/'.
                    break
                self.pos+=1


            """ Ensure nothing follows a trailing star comment."""
            while self.pos < len(self.data) :
                self.pos += 1
                c = self.data[self.pos]
                if c == "\n" :
                    self.newline()
                    break

                if  c != " " and c != "\t":
                    raise  Exception("no syntax may follow trailing comment")



        else :
            """ Consume comment until newline. """
            while True:
                if self.pos == len(self.data) :
                    end = self.pos - 1
                    break
                self.pos += 1
                c = self.data[self.pos]
                if c == "\n":
                    self.newline()
                    end = self.pos - 2 # Account for stepping past the newline.
                    break

        """  Remove trailing whitespace."""
        while end > start and  (self.data[end] == " " or self.data[end] == "\t") :
            end-=1


        if end == start :
            return documentation

        trailing_documentation = self.data[start:end - start + 1]
        if not documentation.strip :
            return trailing_documentation
        return f"{documentation}\n{trailing_documentation}"

    """
    Skips whitespace characters and optionally comments. When this returns, either
    `self.pos == self.data.length` or a non-whitespace character.
    """
    def skip_whitespace(self, skip_comments:bool) :
        while (self.pos < len(self.data) :
            c = self.data[self.pos]
            if c == " " or c == "\t" or c == "\r" or c == "\n" :
                self.pos+=1
                if c == "\n" :
                    self.newline()
            if(skip_comments and  c == '/') :
                self.read_comment()

            return
    """ Call this every time a '\n' is encountered. """
    def newline:
        line+=1
        lineStart = self.pos


  def location(self) = location.at(line + 1, self.pos - lineStart + 1)

  inline def expect(condition: Boolean, location: Location = location(), message: () -> String:
    if (!condition) throw unexpected(message(), location)
  }

  def unexpected(self,
    message: String,
    location: Location? = location()
  ): RuntimeException = throw IllegalStateException("Syntax error in $location: $message")
}













class ProtoParser:
    location: Location
    reader: SyntaxReader
    public_imports: list
    imports: list
    nested_types: list
    services: list
    extends_list: list
    options: list
    declaration_count: int = 0
    syntax: Syntax = None
    package_name: str = None
    prefix: str = ""

    def __int__(self, location: Location, self.data):
        self.reader = SyntaxReader(self.data, location)

    def read_proto_file(self) -> ProtoFileElement:
        while True:
            documentation = self.reader.read_documentation()
            if self.reader.exhausted():
                return ProtoFileElement(self.location, self.package_name, self.syntax, self.imports,
                                        self.public_imports, self.nested_types, self.services, self.extends_list,
                                        self.options)
            declaration = self.read_declaration(documentation, Context.FILE)
            if declaration == TypeElement :
                # TODO: must add check for execption
                duplicate = next((x for x in iter(self.nested_types) if x.name == declaration.name), None)
                if duplicate == None:



